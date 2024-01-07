import pytest
import datetime

from trading_journal.trade_utils import fetch_candle, get_closest_hour

date_data = [(datetime.datetime(2023, 10, 4, 17, 0), datetime.datetime(2023, 10, 4, 17, 0)),
             (datetime.datetime(2023, 10, 8, 18, 0), None),
             (datetime.datetime(2023, 10, 8, 21, 0), datetime.datetime(2023, 10, 8, 21, 0))]

@pytest.mark.parametrize("day,expected_datetime", date_data)
def test_fetch_candle(day, expected_datetime):
    """Test the 'fetch_candle' function"""
    candle = fetch_candle(d=day,
                          pair="AUD_USD",
                          timeframe="H4")
    if expected_datetime is not None:
        assert candle.time == expected_datetime
    else:
        assert candle is None

hour_data =[(9, "H8", 5),
            (21, "H8", 21),
            (17, "H8", 13)]

@pytest.mark.parametrize("solve_hour,timeframe,closest_hour", hour_data)
def test_get_closest_hour(solve_hour,timeframe,closest_hour):
    """Test the 'get_closest_hour' function"""
    assert get_closest_hour(timeframe=timeframe,solve_hour=solve_hour) == closest_hour

def test_get_SLdiff(t_object):
    assert 24.0 == t_object.get_SLdiff()
