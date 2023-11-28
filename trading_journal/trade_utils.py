# Collection of utilities used by the trade.py module
import logging
from datetime import datetime, timedelta

from utils import (substract_pips2price,
                   add_pips2price,
                   calculate_pips,
                   calculate_profit,
                   periodToDelta,
                   try_parsing_date)
from params import counter_params, trade_params
from api.oanda.connect import Connect
from forex.pivot import PivotList
from forex.candle import Candle, CandleList
from forex.harea import HArea

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
        if trade.type == "long":
            new_SR = substract_pips2price(trade.clist.instrument,
                                          trade.SR,
                                          pad)
        elif trade.type == "short":
            new_SR = add_pips2price(trade.clist.instrument,
                                    trade.SR,
                                    pad)
    newcl = trade.clist.slice(start=trade.clist.candles[0].time, 
                              end=trade.start)
    return newcl.get_lasttime(new_SR, type=trade.type)


def calc_period(self) -> int:
    """Number of hours for a certain timeframe"""
    return 24 if self.timeframe == "D" else int(self.timeframe.replace("H",
                                                                        ""))
def gen_datelist(trade: Trade) -> list[datetime]:
    """Generate a range of dates starting at self.start and ending
    trade_params.interval later in order to assess the outcome
    of trade and also the entry time.
    """
    return [trade.start + timedelta(hours=x*calc_period())
            for x in range(0, trade_params.interval)]

def calc_TP(trade: Trade, RR: float) -> float:
    diff = (trade.entry.price - Trade.SL.price) * Trade.RR
    return round(trade.entry.price + diff, 4)

def calc_RR(trade: Trade, TP: float) -> float:
    RR = abs(TP-trade.entry.price)/abs(trade.SL.price-trade.entry.price)
    return round(RR, 2)

def get_trend_i(trade: Trade) -> datetime:
    """Function to calculate the start of the trend"""
    pvLst = PivotList(trade.clist)
    merged_s = pvLst.calc_itrend()

    if trade.type == "long":
        candle = merged_s.get_highest()
    elif trade.type == "short":
        candle = merged_s.get_lowest()

    return candle.time

def get_SLdiff(trade: Trade) -> float:
    """Function to calculate the difference in number of pips between the
    entry and the SL prices.

    Returns:
        number of pips
    """
    diff = abs(trade.entry.price - trade.SL.price)
    number_pips = float(calculate_pips(trade.pair, diff))

    return number_pips

def fetch_candle(d: datetime) -> Candle:
    """Private method to query the API to get a single candle
    if it is not defined in self.clist.

    It will return None if market is closed
    """
    conn = Connect(
        instrument=Trade.pair,
        granularity=Trade.timeframe)
    clO = conn.query(start=d.isoformat(), end=d.isoformat())
    if len(clO.candles) == 1:
        return clO.candles[0]
    elif len(clO.candles) > 1:
        raise Exception("No valid number of candles in "
                        "CandleList")

def check_candle_overlap(cl: Candle, price: float) -> bool:
    """Method to check if Candle 'cl' overlaps 'price'"""
    return cl.l <= price <= cl.h

def end_trade(trade: Trade, connect: bool,
              cl: Candle,
              harea: HArea) -> Trade:
    """End trade"""
    end = None
    if connect is True:
        end = (harea.get_cross_time(candle=cl,
                granularity=trade_params.granularity))
    else:
        end = cl.time
    trade.end = end
    trade.exit = harea.price
    return trade

def finalise_trade(trade: Trade, connect: bool, cl: Candle) -> Trade:
    """Finalise  trade by setting the outcome and calculating profit"""
    if trade.outcome == "success":
        price1 = trade.TP.price
        end_trade(trade,
                  connect=connect,
                  cl=cl,
                  harea=trade.TP)
    if trade.outcome == "failure":
        price1 = trade.SL.price
        end_trade(trade,
                  connect=connect,
                  cl=cl,
                  harea=trade.SL)
    if trade.outcome == "n.a.":
        price1 = cl.c
    trade.pips = calculate_profit(prices=(price1,
                                          trade.entry.price),
                                    type=trade.type,
                                    pair=trade.pair)
    return trade

def init_harea(self, price: float) -> HArea:
    harea_obj = HArea(price=price,
                        instrument=self.pair,
                        pips=trade_params.hr_pips,
                        granularity=self.timeframe)
    return harea_obj

def init_clist(trade: Trade, timeframe: str) -> CandleList:
    delta = periodToDelta(trade_params.trade_period, timeframe)
    start = trade.start
    if not isinstance(start, datetime):
        start = try_parsing_date(start)
    nstart = start - delta

    conn = Connect(
        instrument=trade.pair,
        granularity=timeframe)
    clO = conn.query(nstart.isoformat(), start.isoformat())
    return clO