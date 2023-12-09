import pytest
import datetime

from trading_journal.trade import UnawareTrade
from data_for_tests import trades1, last_times, trades_entered, trades_outcome

trade_details = ["2020-02-19T21:00:00", "EUR_GBP", "long", "D", 0.83585, 0.82467]

@pytest.mark.parametrize(
    "TP, RR, exp_instance",
    [(0.86032, None, UnawareTrade), (None, 1.5, UnawareTrade), (None, None, Exception)],
)
def test_instantiation(TP, RR, exp_instance):
    if exp_instance is UnawareTrade:
        UnawareTrade(
            RR=RR,
            TP=TP,
            start=trade_details[0],
            pair=trade_details[1],
            type=trade_details[2],
            timeframe=trade_details[3],
            entry=trade_details[4],
            SL=trade_details[5],
            init_clist=True
        )
    elif exp_instance == Exception:
        with pytest.raises(Exception):
            UnawareTrade(
                RR=RR,
                TP=TP,
                start=trade_details[0],
                pair=trade_details[1],
                type=trade_details[2],
                timeframe=trade_details[3],
                entry=trade_details[4],
                SL=trade_details[5],
                init_clist=True
            )

def test_init_clist():
    """This test checks the init_clist function"""
    td = UnawareTrade(
        TP=0.86032,
        start=trade_details[0],
        pair=trade_details[1],
        type=trade_details[2],
        timeframe=trade_details[3],
        entry=trade_details[4],
        SL=trade_details[5],
        init_clist=True,
    )
    assert len(td.clist.candles) == 4104


trade_data1 = [(*trade, pip) for trade, pip in zip(trades1, last_times)]

@pytest.mark.parametrize("start,type,SR,SL,TP,entry,lasttime", trade_data1)
def test_get_lasttime(start, type, SR, SL, TP, entry, lasttime, clO_pickled):
    """Check function get_lasttime"""
    t = UnawareTrade(
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
    t = UnawareTrade(
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


# add a non initialised trade
trades_for_test_initialise = trades1[:]
trades_for_test_initialise.append(("2018-12-23 22:00:00", "long", 0.70112, 0.69637, 0.72756, 0.70895))
entry_data = [(True, "2016-12-29T08:00:00"),
              (True,"2017-04-12T19:00:00"), 
              (True,"2017-09-12T01:00:00"),
              (True, "2018-05-04T01:00:00"),
              (False, "n.a.")]
trade_data2 = [(*trade, pip) for trade, pip in zip(trades_for_test_initialise, entry_data)]

@pytest.mark.parametrize("start,type,SR,SL,TP,entry,entry_data", trade_data2)
def test_initialise(start, type, SR, SL, TP, entry, entry_data, clO_pickled):
    t = UnawareTrade(
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
        clist_tm=clO_pickled)
    t.initialise()
    assert t.entered == entry_data[0]
    if hasattr(t, "entry_time"):
        assert t.entry_time == entry_data[1]

trades_for_entry_onrsi = trades1[:]
trades_for_entry_onrsi.append(("2017-07-25 22:00:00", "short", 0.79743, 0.80577, 0.77479, 0.79343))

is_on_rsi = [False, False, False, False, True]
trade_data3 = [(*trade, pip) for trade, pip in zip(trades_for_entry_onrsi, is_on_rsi)]
@pytest.mark.parametrize("start,type,SR,SL,TP,entry,entry_onrsi", trade_data3)
def test_is_entry_onrsi(start, type, SR, SL, TP, entry, entry_onrsi, clO_pickled):
    """Test is_entry_onrsi function"""
    t = UnawareTrade(
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


trade_data1 = [(*trade, pip) for trade, pip in zip(trades_entered, trades_outcome)]

@pytest.mark.parametrize("start,type,SR,SL,TP,entry,trades_outcome", trade_data1)
def test_run(start, type, SR, SL, TP, entry, trades_outcome, clOH8_2019_pickled, clO_pickled):
    """Test 'run' function"""
    print(trades_outcome)
    t = UnawareTrade(
        id="test",
        start=start,
        pair="AUD_USD",
        timeframe="H8",
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        clist=clOH8_2019_pickled,
        clist_tm=clO_pickled)
    t.initialise()
    t.run(connect=False)
    assert t.outcome == trades_outcome[0]
    assert t.pips == trades_outcome[1]

