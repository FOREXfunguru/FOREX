# Collection of utilities used by the trade.py module
import logging
from datetime import datetime, timedelta

from utils import (periodToDelta,
                   try_parsing_date,
                   add_pips2price,
                   substract_pips2price)
from params import trade_params
from api.oanda.connect import Connect
from forex.candle import Candle, CandleList

t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)


def calc_period(timeframe: str) -> int:
    """Number of hours for a certain timeframe"""
    return 24 if timeframe == "D" else int(timeframe.replace("H",
                                                             ""))

def check_timeframes_fractions(timeframe1: str, timeframe2: str) -> float:
    """Get the number of times 'timeframe1' is contained in 'timeframe2'"""
    hours1 = calc_period(timeframe1)
    hours2 = calc_period(timeframe2)

    return float(hours1/hours2)


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

        result_datetime = dt - timedelta(hours=calc_period(timeframe))
        dt = dt.replace(day=result_datetime.day,
                        month=result_datetime.month,
                        hour=closest_hour,
                        year=result_datetime.year,
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
        new_d = None
        if d.hour%2 > 0:
            new_d = d+timedelta(hours=1)
        else:
            new_d = d-timedelta(hours=1)
        #  try with hour-1 to deal with time shifts
        cl = fetch_candle(d=new_d,
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

def adjust_SL(pair: str, type: str, list_candles = list[Candle],
              pips_offset: int=10) -> float:
    """Adjust SL to minimum in 'list_candles'.
    
    Arguments:
        pair: Instrument
        type: Trade type (short/long)
        list_candles: List of candles
        pips_offset: Number of pips to offset to obj.h and obj.l
    """
    if type == "short":
        max_candle = max(list_candles, key=lambda obj: obj.h)
        new_high = add_pips2price(pair, max_candle.h, pips_offset)
        return new_high

    if type == "long":
        min_candle = min(list_candles, key=lambda obj: obj.l)
        new_low = substract_pips2price(pair, min_candle.l, pips_offset)
        return new_low