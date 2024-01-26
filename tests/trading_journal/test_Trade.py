import pytest
import datetime

from trading_journal.open_trade import Trade
from data_for_tests import (trades1,
                            last_times)


trade_data1 = [(*trade, pip) for trade, pip in zip(trades1, last_times)]

@pytest.mark.parametrize("start,type,SR,SL,TP,entry,lasttime", trade_data1)
def test_get_lasttime(start, type, SR, SL, TP, entry, lasttime, clO_pickled):
    """Check function get_lasttime"""
    t = Trade(
        id="test",
        start=start,
        pair="AUD_USD",
        timeframe="D",
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        clist=clO_pickled)

    assert t.get_lasttime() == lasttime

@pytest.mark.parametrize(
    "start," "type," "SR," "SL," "TP," "entry," "lasttime",
    [
        (
            "2017-12-10 22:00:00",
            "long",
            0.74986,
            0.74720,
            0.76521,
            0.75319,
            datetime.datetime(2017, 6, 1, 21, 0),
        ),
        (
            "2017-03-21 22:00:00",
            "short",
            0.77103,
            0.77876,
            0.73896,
            0.76717,
            datetime.datetime(2016, 4, 19, 21, 0),
        ),
    ],
)
def test_get_lasttime_with_pad(start, type, SR, SL, TP, entry, lasttime, clO_pickled):
    """Check function get_lasttime"""
    t = Trade(
        id="test",
        start=start,
        pair="AUD_USD",
        timeframe="D",
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        clist=clO_pickled,
    )

    assert t.get_lasttime(pad=30) == lasttime

trades_for_entry_onrsi = trades1[:]
trades_for_entry_onrsi.append(("2017-07-25 22:00:00", "short", 0.79743, 0.80577, 0.77479, 0.79343))

is_on_rsi = [False, False, False, False, True]
trade_data3 = [(*trade, pip) for trade, pip in zip(trades_for_entry_onrsi, is_on_rsi)]
@pytest.mark.parametrize("start,type,SR,SL,TP,entry,entry_onrsi", trade_data3)
def test_is_entry_onrsi(start, type, SR, SL, TP, entry, entry_onrsi, clO_pickled):
    """Test is_entry_onrsi function"""
    t = Trade(
        id="test",
        start=start,
        pair="AUD_USD",
        timeframe="D",
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        clist=clO_pickled,
        clist_tm=clO_pickled
    )
    newclist = t.clist
    newclist.calc_rsi()
    t.clist = newclist
    assert entry_onrsi == t.is_entry_onrsi()