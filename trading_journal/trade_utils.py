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

def get_closest_hour(timeframe: str, solve_hour: int) -> int:
    """Get the closest hour to 'solve_hour'"""
    time_ranges_dict = {
            "H4": [21, 1, 5, 9, 13, 17],
            "H8": [21, 5, 13],
            "H12": [21, 9],
            "D" : [21]}
    filtered_hours = [hour for hour in time_ranges_dict[timeframe] if (solve_hour - hour) >= 0]
    if filtered_hours:
        closest_hour = min(filtered_hours, key=lambda x: solve_hour - x)
    else:
        closest_hour = 21
    return closest_hour

def process_start(dt: datetime, timeframe: str) -> datetime:
    """Round fractional times for Trade.start.
    
    Returns:
    Rounded aligned datetime
    """
    closest_hour = get_closest_hour(timeframe=timeframe, solve_hour=dt.time().hour)

    if closest_hour== 21 and dt.time().hour >= 0 and not dt.time().hour in [22, 23]:
        day = dt.day
        dt = dt.replace(day=day-1,
                        hour=closest_hour,
                        minute=0,
                        second=0)
    else:
        dt = dt.replace(hour=closest_hour,
                        minute=0,
                        second=0)
    return dt

def gen_datelist(start: datetime, timeframe: str) -> list[datetime]:
    """Generate a range of dates starting at start and ending
    trade_params.interval later in order to assess the outcome
    of trade and also the entry time.
    """
    return [start + timedelta(hours=x*calc_period(timeframe))
            for x in range(0, trade_params.interval)]


def fetch_candle_api(d: datetime, pair: str, timeframe: str):
    cl = None
    cl = fetch_candle(d=d,
                      pair=pair,
                      timeframe=timeframe)
    if cl is None:
        #  try with hour-1 to deal with time shifts
        cl = fetch_candle(d=d-timedelta(hours=1),
                          pair=pair,
                          timeframe=timeframe)
    return cl


def fetch_candle(d: datetime, pair: str, timeframe: str) -> Candle:
    """Private method to query the API to get a single candle
    if it is not defined in Trade.clist.
    """
    conn = Connect(
        instrument=pair,
        granularity=timeframe)
    # substract one min to be sure we fetch the right candle
    start = d - timedelta(minutes=1)
    clO = conn.query(start=start.isoformat(), end=start.isoformat())

    if len(clO.candles) == 1:
        if clO.candles[0].time != d:
            # return None if candle is not equal to 'd'
            return
        return clO.candles[0]
    if len(clO.candles) > 1:
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