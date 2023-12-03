# Collection of utilities used by the trade.py module
import logging
from datetime import datetime, timedelta

from utils import (periodToDelta,
                   try_parsing_date)
from params import trade_params
from api.oanda.connect import Connect
from forex.candle import Candle, CandleList

t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)


def calc_period(timeframe: str) -> int:
    """Number of hours for a certain timeframe"""
    return 24 if timeframe == "D" else int(timeframe.replace("H",
                                                             ""))


def gen_datelist(start: datetime, timeframe: str) -> list[datetime]:
    """Generate a range of dates starting at start and ending
    trade_params.interval later in order to assess the outcome
    of trade and also the entry time.
    """
    return [start + timedelta(hours=x*calc_period(timeframe))
            for x in range(0, trade_params.interval)]


def fetch_candle(d: datetime, pair: str, timeframe: str) -> Candle:
    """Private method to query the API to get a single candle
    if it is not defined in Trade.clist.
    """
    conn = Connect(
        instrument=pair,
        granularity=timeframe)
    clO = conn.query(start=d.isoformat(), end=d.isoformat())
    if len(clO.candles) == 1:
        return clO.candles[0]
    elif len(clO.candles) > 1:
        raise Exception("No valid number of candles in "
                        "CandleList")


def check_candle_overlap(cl: Candle, price: float) -> bool:
    """Method to check if Candle 'cl' overlaps 'price'"""
    return cl.l <= price <= cl.h


def init_clist(timeframe: str, pair: str, start: datetime) -> CandleList:
    delta = periodToDelta(trade_params.trade_period, timeframe)
    if not isinstance(start, datetime):
        start = try_parsing_date(start)
    nstart = start - delta

    conn = Connect(
        instrument= pair,
        granularity=timeframe)
    return conn.query(nstart.isoformat(), start.isoformat())