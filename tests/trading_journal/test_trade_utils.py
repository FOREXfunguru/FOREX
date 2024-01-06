import pytest
import datetime
import pdb

from trading_journal.trade_utils import fetch_candle

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


def test_get_SLdiff(t_object):
    assert 24.0 == t_object.get_SLdiff()
