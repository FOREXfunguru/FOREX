# Collection of utilities used by the Trade object
import logging
import pdb
import datetime as dt

from utils import *
from params import counter_params, tradebot_params, trade_params
from forex.candlelist_utils import *
from forex.pivot import PivotList
from forex.candle import CandleList
from trading_journal.trade import Trade
from typing import Tuple

# create logger
t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)

def is_entry_onrsi(trade: Trade)->bool:
    '''Function to check if tObj.start is on RSI.

    Arguments:
        trade : Trade object used for the calculation

    Returns:
        True if tObj.start is on RSI (i.e. RSI>=70 or RSI<=30)
    '''
    if trade.clist.candles[-1].rsi >= 70 or trade.clist.candles[-1].rsi <= 30:
        return True
    else:
        return False

def get_lasttime(trade: Trade, pad: int=0):
        '''Function to calculate the last time price has been above/below
        a certain HArea.

        Arguments:
            trade : Trade object used for the calculation
            pad : Add/substract this number of pips to trade.SR 
        '''
        new_SR = trade.SR
        if pad > 0:
            if trade.type == 'long':
                new_SR = substract_pips2price(trade.clist.instrument,
                                              trade.SR,
                                              pad)
            elif trade.type == 'short':
                new_SR = add_pips2price(trade.clist.instrument,
                                        trade.SR,
                                        pad)
        newcl = trade.clist.slice(start=trade.clist.candles[0].time, end=trade.start)
        return newcl.get_lasttime(new_SR, type=trade.type)

def get_max_min_rsi(trade)->float:
    """Function to calculate the max or min RSI for CandleList slice
    going from trade.start-CONFIG.getint('counter', rsi_period') to trade.start.

    Returns:
        The max (if short trade) or min (long trade) rsi value
        in the candlelist
    """
    t_logger.debug("Running set_max_min_rsi")

    ix = counter_params.rsi_period
    sub_clist = trade.clist.candles[-ix:]
    rsi_list = [x.rsi for x in sub_clist]
    first = None
    for x in reversed(rsi_list):
        if first is None:
            first = x
        elif trade.type == 'short':
            if x > first:
                first = x
        elif trade.type == 'long':
            if x < first:
                first = x

    t_logger.debug("Done set_max_min_rsi")

    return round(first, 2)

def calc_trade_session(trade):
    '''
    Function to calculate the trade session (European, Asian,
    NAmerican) the trade was taken

    Arguments:
        trade : Trade object used for the calculation

    Returns:
        str Comma-separated string with different sessions: i.e. european,asian
                                                            or namerican, etc...
        I will return n.a. if self.entry_time is not defined
    '''
    if not hasattr(trade, 'entry_time'):
        return "n.a."
    dtime = dt.datetime.strptime(trade.entry_time, '%Y-%m-%dT%H:%M:%S')
    # define the different sessions time boundaries
    a_u2 = dt.time(int(7), int(0), int(0))
    a_l2 = dt.time(int(0), int(0), int(0))
    a_u1 = dt.time(int(23), int(59), int(59))
    a_l1 = dt.time(int(23), int(0), int(0))
    e_u = dt.time(int(15), int(0), int(0))
    e_l = dt.time(int(7), int(0), int(0))
    na_u = dt.time(int(19), int(0), int(0))
    na_l = dt.time(int(12), int(0), int(0))

    sessions = []
    session_seen = False
    if dtime.time() >= a_l1 and dtime.time() <= a_u1:
        sessions.append('asian')
        session_seen = True
    if dtime.time() >= a_l2 and dtime.time() <= a_u2:
        sessions.append('asian')
        session_seen = True
    if dtime.time() >= e_l and dtime.time() <= e_u:
        sessions.append('european')
        session_seen = True
    if dtime.time() >= na_l and dtime.time() <= na_u:
        sessions.append('namerican')
        session_seen = True
    if session_seen is False:
        sessions.append('nosession')
    return ",".join(sessions)

def calc_pips_c_trend(trade: Trade)->float:
    '''Function to calculate the pips_c_trend value.
    This value represents the average number of pips for each candle from
    trade.trend_i up to trade.start

    Arguments:
        trade : Used for the calculation
    '''
    sub_cl = trade.clist.slice(start=trade.get_trend_i(),
                               end =trade.start)

    pips_c_trend = sub_cl.get_length_pips()/sub_cl.get_length_candles()

    return round(pips_c_trend, 1)

def get_trade_type(dt, clObj: CandleList)->str:
    """Function to get the type of a Trade (short/long).

    Arguments:
        dt : datetime object
             This will be the datetime for the IC candle
        clObj : CandleList used for calculation

    Returns:
        type (short/long)
    """
    if dt != clObj.candles[-1].time:
        dt = clObj.candles[-1].time

    # increate sensitivity for pivot detection
    PL= PivotList(clObj, th_bounces=trade_params.th_bounces)

    # now, get the Pivot matching the datetime for the IC+1 candle
    if PL.pivots[-1].candle.time != dt:
        raise Exception("Last pivot time does not match the passed datetime")
    # check the 'type' of Pivot.pre segment
    direction = PL.pivots[-1].pre.type

    if direction == -1 :
        return 'long'
    elif direction == 1 :
        return 'short'
    else:
        raise Exception("Could not guess the file type")

def calc_adr(trade: Trade)->float:
    """
    Function to calculate the ATR (avg timeframe rate)
    from trade.start - CONFIG.getint('trade', 'period_atr')

    Arguments:
        trade : Used for the calculation

    Returns:
        ATR for selected period
    """
    delta_period = periodToDelta(CONFIG.getint('trade', 'period_atr'),
                                 trade.timeframe)
    delta_1 = periodToDelta(1, trade.timeframe)
    start = trade.start - delta_period  # get the start datetime
    end = trade.start + delta_1  # increase trade.start by one candle to include trade.start

    c_list = trade.period.slice(start, end)

    return calc_atr(c_list)

def prepare_trade(tb_obj, type: str, SL: float, ic, harea_sel, delta, add_pips: int=None, TP: float=None)->Trade:
    '''Prepare a Trade object and check if it is taken.

    Arguments:
        tb_obj : TradeBot object
        type : Type of trade. 'short' or 'long'
        SL : Adjusted (by '__get_trade_type') SL price
        ic : Candle object
             Indecision candle for this trade
        harea_sel : HArea of this trade
        delta : Timedelta object corresponding to
                the time that needs to be increased
        add_pips : Number of pips above/below SL and entry
            price to consider for recalculating
            the SL and entry
        TP : Take profit value
    '''
    startO = ic.time + delta
    if type == 'short':
        # entry price will be the low of IC
        entry_p = ic.l
        if add_pips is not None:
            SL = round(add_pips2price(tb_obj.pair,
                                      SL, add_pips), 4)
            entry_p = round(substract_pips2price(tb_obj.pair,
                                                 entry_p, add_pips), 4)
    elif type == 'long':
        # entry price will be the high of IC
        entry_p = ic.h
        if add_pips is not None:
            entry_p = add_pips2price(tb_obj.pair,
                                     entry_p, add_pips)
            SL = substract_pips2price(tb_obj.pair,
                                      SL, add_pips)

    startO = ic.time+delta
    t = Trade(
        id='{0}.bot'.format(tb_obj.pair),
        start=startO.strftime('%Y-%m-%d %H:%M:%S'),
        pair=tb_obj.pair,
        timeframe=tb_obj.timeframe,
        type=type,
        entry=entry_p,
        SR=harea_sel.price,
        SL=SL,
        TP=TP,
        RR=tradebot_params.RR,
        strat='counter')
    return t

def validate_trade(t: Trade)->bool:
    """Check if Trade if valid in terms of SL, entry, TP"""
    if t.TP > t.entry> t.SL and t.type == 'long': 
        return True
    elif t.TP < t.entry < t.SL and t.type == 'short':
        return True
    return False

def adjust_SL_pips(price: float, type: str, pair: str, no_pips: int=100)->float:
    '''Function to adjust the SL price
    to the most recent highest high/lowest low.

    Arguments:
        price : SL that will be adjusted
        type : Trade type ('long'/ 'short').
        pair: Pair
        no_pips: Number of pips to add the S/L value.
    
    Returns:
        adjusted SL
    '''
    if type == 'long':
        SL = substract_pips2price(pair, price, no_pips )
    else:
        SL = add_pips2price(pair, price, no_pips )
        
    return SL

def adjust_SL_nextSR(SRlst: HAreaList, sel_ix: int, type: str)->Tuple[float, float]:
    '''Function to calculate the TP and SL prices to the next SR areas'''
    TP, SL = None, None
    try:
        if type == 'long':
            SL = SRlst.halist[sel_ix-1].price
            TP = SRlst.halist[sel_ix+1].price
            if sel_ix-1 < 0:
                SL = None
        else:
            TP = SRlst.halist[sel_ix-1].price
            SL = SRlst.halist[sel_ix+1].price
            if sel_ix-1 < 0:
                TP = None
    except:
        t_logger.warning(f"sel_ix error: {sel_ix}. Trying with adjust_SL_pips")

    return SL, TP

def adjust_SL_candles(type: str, clObj: CandleList, number: int=7)->float:
    '''Function to adjust the SL price
    to the most recent highest high/lowest low.

    Arguments:
        type : Trade type ('long'/ 'short')
        clObj : CandleList obj
        number : Number of candles to go back
                 to adjust the SL.

    Returns:
        adjusted SL
    '''
    SL, ix = None, 0
    if not clObj.candles:
        raise Exception("No candles in CandleList. Can't calculate the SL")
    for c in reversed(clObj.candles):
        # go back 'number' candles
        if ix == number:
            break
        ix += 1
        if type == 'short':
            if SL is None:
                SL = c.h
            elif c.h > SL:
                SL = c.h
        if type == 'long':
            if SL is None:
                SL = c.l
            if c.l < SL:
                SL = c.l
    return SL

def calculate_profit(trade: Trade)->float:
    '''Function to calculate the profit of a certain
    trade. Profit is defined as:
    if abs(t.entry-t.SL) is = 1
    Then abs(t.end-t.entry) is calculated taking this t.entry-t.SL
    as the reference diff

    Arguments:
        trade : Trade object
    '''
    R = abs(float(trade.entry) - float(trade.SL))
    mult = None
    if trade.outcome == 'success':
        mult = 1
    elif trade.outcome == 'failure':
        mult = -1
    diff = abs(float(trade.exit) - float(trade.entry))

    profit = mult * (diff / R)
    return round(profit, 2)