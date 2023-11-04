# Collection of utilities used by the Trade object
import logging

from datetime import datetime
from utils import substract_pips2price, add_pips2price, calculate_pips
from params import counter_params, tradebot_params, trade_params
from forex.pivot import PivotList
from forex.candle import CandleList, Candle
from forex.harea import HAreaList
from trading_journal.trade import Trade
from typing import Tuple

# create logger
t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)


def is_entry_onrsi(trade: Trade) -> bool:
    """Function to check if tObj.start is on RSI.

    Arguments:
        trade : Trade object used for the calculation

    Returns:
        True if tObj.start is on RSI (i.e. RSI>=70 or RSI<=30)
    """
    if trade.clist.candles[-1].rsi >= 70 or trade.clist.candles[-1].rsi <= 30:
        return True
    else:
        return False


def get_lasttime(trade: Trade, pad: int = 0):
    """Function to calculate the last time price has been above/below
    a certain HArea.

    Arguments:
        trade : Trade object used for the calculation
        pad : Add/substract this number of pips to trade.SR 
    """
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
    newcl = trade.clist.slice(start=trade.clist.candles[0].time, 
                              end=trade.start)
    return newcl.get_lasttime(new_SR, type=trade.type)


def get_max_min_rsi(trade) -> float:
    """Function to calculate the max or min RSI for CandleList slice
    going from trade.start-counter_params.rsi_period
    to trade.start.

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


def calc_trade_session(trade) -> str:
    """Function to calculate the trade session (European, Asian,
    NAmerican) the trade was taken

    Arguments:
        trade : Trade object used for the calculation

    Returns:
        Comma-separated string with different
        sessions: i.e. european,asian or namerican, etc...
        It will return n.a. if self.entry_time is not defined
    """
    if not hasattr(trade, 'entry_time'):
        return "n.a."
    dtime = datetime.datetime.strptime(trade.entry_time, '%Y-%m-%dT%H:%M:%S')
    # define the different sessions time boundaries
    a_u2 = datetime.time(int(7), int(0), int(0))
    a_l2 = datetime.time(int(0), int(0), int(0))
    a_u1 = datetime.time(int(23), int(59), int(59))
    a_l1 = datetime.time(int(23), int(0), int(0))
    e_u = datetime.time(int(15), int(0), int(0))
    e_l = datetime.time(int(7), int(0), int(0))
    na_u = datetime.time(int(19), int(0), int(0))
    na_l = datetime.time(int(12), int(0), int(0))

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


def calc_pips_c_trend(trade: Trade) -> float:
    """Function to calculate the pips_c_trend value.
    This value represents the average number of pips for each candle from
    trade.trend_i up to trade.start

    Arguments:
        trade : Used for the calculation
    """
    sub_cl = trade.clist.slice(start=trade.get_trend_i(),
                               end=trade.start)

    pips_c_trend = sub_cl.get_length_pips()/sub_cl.get_length_candles()

    return round(pips_c_trend, 1)


def get_trade_type(dt, clObj: CandleList) -> str:
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
    PL = PivotList(clObj, th_bounces=trade_params.th_bounces)

    # now, get the Pivot matching the datetime for the IC+1 candle
    if PL.pivots[-1].candle.time != dt:
        raise Exception("Last pivot time does not match the passed datetime")
    # check the 'type' of Pivot.pre segment
    direction = PL.pivots[-1].pre.type

    if direction == -1:
        return "long"
    elif direction == 1:
        return "short"
    else:
        raise Exception("Could not guess the file type")


def prepare_trade(tb_obj, start: datetime, type: str, SL: float, ic: Candle,
                  harea_sel, add_pips: int = None, TP: float = None) -> Trade:
    """Prepare a Trade object and check if it is taken.

    Arguments:
        tb_obj : TradeBot object
        start : Start datetime for the trade
        type : Type of trade. ['short','long']
        SL : Adjusted (by '__get_trade_type') SL price
        ic: Indecission candle
        harea_sel : HArea of this trade
        add_pips : Number of pips above/below SL and entry
                   price to consider for recalculating
                   the SL and entry
        TP : Take profit value
    """
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

    t = Trade(
        id='{0}.bot'.format(tb_obj.pair),
        start=start.strftime('%Y-%m-%d %H:%M:%S'),
        pair=tb_obj.pair,
        timeframe=tb_obj.timeframe,
        type=type,
        entry=entry_p,
        SR=harea_sel.price,
        SL=SL,
        TP=TP,
        RR=tradebot_params.RR)
    return t


def validate_trade(t: Trade) -> bool:
    """Check if Trade if valid in terms of SL, entry, TP"""
    if t.TP > t.entry > t.SL and t.type == 'long':
        return True
    elif t.TP < t.entry < t.SL and t.type == 'short':
        return True
    return False


def adjust_SL_pips(candle: Candle,
                   type: str, pair: str,
                   no_pips: int = 100) -> float:
    """Function to adjust the SL price
    to the most recent highest high/lowest low.

    Arguments:
        candle : Candle object for which SL will be adjusted
        type : Trade type ('long'/ 'short').
        pair: Pair
        no_pips: Number of pips to add to the highest/lowest of 
        the candle to calculate the S/L value.

    Returns:
        adjusted SL
    """
    if type == 'long':
        price = candle.l
        SL = substract_pips2price(pair, price, no_pips)
    else:
        price = candle.h
        SL = add_pips2price(pair, price, no_pips)

    return SL


def adjust_SL_nextSR(SRlst: HAreaList,
                     sel_ix: int,
                     type: str) -> Tuple[float, float]:
    """Function to calculate the TP and SL prices to the next SR areas"""
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
    except Exception:
        t_logger.warning(f"sel_ix error: {sel_ix}. Trying with adjust_SL_pips")

    return SL, TP


def adjust_SL_candles(type: str, clObj: CandleList, number: int = 7) -> float:
    """Function to adjust the SL price
    to the most recent highest high/lowest low.

    Arguments:
        type : Trade type ('long'/ 'short')
        clObj : CandleList obj
        number : Number of candles to go back
                 to adjust the SL.

    Returns:
        adjusted SL
    """
    SL, ix = None, 0
    if not clObj.candles:
        raise Exception("No candles in CandleList. Can't calculate the SL")
    for c in reversed(clObj.candles):
        # go back 'number' candles
        if ix == number:
            break
        ix += 1
        if type == "short":
            if SL is None:
                SL = c.h
            elif c.h > SL:
                SL = c.h
        if type == "long":
            if SL is None:
                SL = c.l
            if c.l < SL:
                SL = c.l
    return SL
