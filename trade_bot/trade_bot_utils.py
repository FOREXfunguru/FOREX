import datetime
from typing import Tuple

from forex.harea import HArea, HAreaList
from forex.candle import Candle, CandleList
from trading_journal.trade import Trade
from forex.pivot import PivotList
from params import trade_params

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
    if type == "long":
        price = candle.l
        SL = substract_pips2price(pair, price, no_pips)
    else:
        price = candle.h
        SL = add_pips2price(pair, price, no_pips)

    return SL

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
    if type == "short":
        # entry price will be the low of IC
        entry_p = ic.l
        if add_pips is not None:
            SL = round(add_pips2price(tb_obj.pair,
                                      SL, add_pips), 4)
            entry_p = round(substract_pips2price(tb_obj.pair,
                                                 entry_p, add_pips), 4)
    elif type == "long":
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

def adjust_SL_nextSR(SRlst: HAreaList,
                     sel_ix: int,
                     type: str) -> Tuple[float, float]:
    """Function to calculate the TP and SL prices to the next SR areas"""
    TP, SL = None, None
    try:
        if type == "long":
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



