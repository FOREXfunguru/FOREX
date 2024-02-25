import pytest
import logging

from datetime import datetime
from api.oanda.connect import Connect
from trading_journal.trade_utils import process_start


@pytest.fixture
def conn_o():
    log = logging.getLogger("connect_o")
    log.debug("Create a Connect object")

    conn = Connect(instrument="AUD_USD", granularity="D")
    return conn


def test_query_s_e(conn_o):
    log = logging.getLogger("test_query_s_e")
    log.debug("Test for 'query' function with a start and end datetimes")
    clO = conn_o.query("2018-11-16T22:00:00", "2018-11-20T22:00:00")
    assert clO.instrument == "AUD_USD"
    assert clO.granularity == "D"
    assert len(clO) == 3
    assert isinstance(clO.times[0], datetime)


def test_query_c(conn_o):
    log = logging.getLogger("test_query_c")
    log.debug("Test for 'query' function with a start and count parameters")
    clO = conn_o.query("2018-11-16T22:00:00", count=1)
    assert clO.instrument == "AUD_USD"
    assert clO.granularity == "D"
    assert len(clO) == 1


@pytest.mark.parametrize(
    "i,g,s,e,l",
    [
        ("GBP_NZD", "D", "2018-11-23T22:00:00", "2019-01-02T22:00:00", 27),
        ("GBP_AUD", "D", "2002-11-23T22:00:00", "2007-01-02T22:00:00", 877),
        ("EUR_NZD", "D", "2002-11-23T22:00:00", "2007-01-02T22:00:00", 881),
        ("AUD_USD", "D", "2015-01-25T22:00:00", "2015-01-26T22:00:00", 2),
        ("AUD_USD", "D", "2018-11-16T22:00:00", "2018-11-20T22:00:00", 3),
        ("AUD_USD", "H12", "2018-11-12T10:00:00", "2018-11-14T10:00:00", 5),
        # End date falling in the daylight savings discrepancy(US/EU) period
        ("AUD_USD", "D", "2018-03-26T22:00:00", "2018-03-29T22:00:00", 4),
        # End date falling in Saturday at 21h
        ("AUD_USD", "D", "2018-05-21T21:00:00", "2018-05-26T21:00:00", 4),
        # Start and End data fall on closed market
        ("AUD_USD", "D", "2018-04-27T21:00:00", "2018-04-28T21:00:00", 0),
        # Start date before the start of historical record
        ("AUD_USD", "H12", "2000-11-21T22:00:00", "2002-06-15T22:00:00", 32),
    ],
)
def test_m_queries(i, g, s, e, l):
    log = logging.getLogger("test_query_ser")
    log.debug(
        "Test for 'query' function with a mix of " "instruments and different datetimes"
    )

    conn = Connect(instrument=i, granularity=g)

    clO = conn.query(start=s, end=e)
    assert len(clO) == l


def test_query_M30():
    log = logging.getLogger("test_query_M30")
    log.debug("Test for 'query' function with granularity M30")

    conn = Connect(instrument="AUD_USD", granularity="M30")

    clO = conn.query(start="2018-05-21T21:00:00", end="2018-05-23T21:00:00")
    assert len(clO) == 97


def test_validate_datetime():
    log = logging.getLogger("test_validate_datetime")
    log.debug("Test for function with wrong datetime format")

    conn = Connect(instrument="AUD_USD", granularity="D")

    with pytest.raises(ValueError):
        conn.validate_datetime("2018-05-23T21")


def test_query_in_future():
    """Query with a future datetime"""
    timeframe = "D"
    now = datetime.now()
    aligned_start = process_start(dt=now, timeframe=timeframe).isoformat().split(".")[0]

    conn = Connect(instrument=timeframe, granularity="AUD_USD")
    assert conn.query(aligned_start, count=1).candles == []


date_data = [
    (datetime(2023, 10, 4, 17, 0), datetime(2023, 10, 4, 17, 0)),
    (datetime(2023, 10, 8, 18, 0), None),
    (datetime(2023, 10, 8, 21, 0), datetime(2023, 10, 8, 21, 0)),
    (datetime(2022, 11, 30, 21, 0), datetime(2022, 11, 30, 22, 0)),
    (datetime(2022, 11, 18, 21, 0), None)
]


@pytest.mark.parametrize("day,expected_datetime", date_data)
def test_fetch_candle(day, expected_datetime):
    conn = Connect(instrument="AUD_USD", granularity="H4")
    candle = conn.fetch_candle(d=day)
    if expected_datetime is not None:
        assert candle.time == expected_datetime
    else:
        assert candle is None
