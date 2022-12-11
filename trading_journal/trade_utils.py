# Collection of utilities used by the Trade object
import logging
import pdb
import datetime as dt

from utils import *
from params import counter_params, tradebot_params
from forex.candlelist_utils import *
from forex.pivot import PivotList
from trading_journal.trade import Trade

# create logger
t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)

def is_entry_onrsi(trade):
    '''Function to check if tObj.start is on RSI.

    Arguments:
        trade : Trade object
                Used for the calculation

    Returns:
        True if tObj.start is on RSI (i.e. RSI>=70 or RSI<=30)
        False otherwise
    '''
    if trade.clist.candles[-1].rsi >= 70 or trade.clist.candles[-1].rsi <= 30:
        return True
    else:
        return False

def get_lasttime(trade):
        '''
        Function to calculate the last time price has been above/below
        a certain HArea.

        Arguments:
            trade : Trade object
                    Used for the calculation

        Returns:
            Datetime
        '''
        t_logger.debug("Running get_lasttime")

        return trade.clist.get_lasttime(trade.SR)

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
        trade : Trade object
                Used for the calculation

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

def calc_pips_c_trend(trade)->float:
    '''Function to calculate the pips_c_trend value.
    This value represents the average number of pips for each candle from
    trade.trend_i up to trade.start

    Arguments:
        trade : Trade object
                Used for the calculation
    '''
    pdb.set_trace()
    sub_cl = trade.clist.slice(start=trade.get_trend_i(),
                               end =trade.start)

    pips_c_trend = sub_cl.get_length_pips()/sub_cl.get_length_candles()

    return round(pips_c_trend, 1)

def get_trade_type(dt, clObj)->str:
    """Function to get the type of a Trade (short/long).

    Arguments:
        dt : datetime object
             This will be the datetime for the IC candle
        clObj : CandleList object

    Returns:
        type (short'/'long')
    """
    if dt != clObj.candles[-1].time:
        dt = clObj.candles[-1].time

    PL= PivotList(clObj)

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

def calc_adr(trade)->float:
    """
    Function to calculate the ATR (avg timeframe rate)
    from trade.start - CONFIG.getint('trade', 'period_atr')

    Arguments:
        trade : Trade object
                Used for the calculation

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

def prepare_trade(tb_obj, type: str, SL: float, ic, harea_sel, delta, add_pips):
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
            the SL and entry. Default : None

    Returns:
        Trade object
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
        RR=tradebot_params.RR,
        strat='counter')
    return t

def adjust_SL(type: str, clObj, number: int=7)->float:
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
    SL = None
    ix = 0
    for c in reversed(clObj.candles):
        # go back 'number' candles
        if ix == number:
            break
        ix += 1
        price = c.c
        if SL is None:
            SL = price
            continue
        if type == 'short':
            if price > SL:
                SL = price
        if type == 'long':
            if price < SL:
                SL = price
    return SL

def calculate_profit(trade)->float:
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