import pytest
import datetime
import pdb

from trading_journal.trade import Trade
from data_for_tests import trades, trades1, trades2, last_times

trade_details = ["2020-02-19T21:00:00", "EUR_GBP", "long", "D", 0.83585, 0.82467]

@pytest.mark.parametrize(
    "TP, RR, exp_instance",
    [(0.86032, None, Trade), (None, 1.5, Trade), (None, None, Exception)],
)
def test_instantiation(TP, RR, exp_instance):
    if exp_instance is Trade:
        Trade(
            RR=RR,
            TP=TP,
            start=trade_details[0],
            pair=trade_details[1],
            type=trade_details[2],
            timeframe=trade_details[3],
            entry=trade_details[4],
            SL=trade_details[5],
        )
    elif exp_instance == Exception:
        with pytest.raises(Exception):
            Trade(
                RR=RR,
                TP=TP,
                start=trade_details[0],
                pair=trade_details[1],
                type=trade_details[2],
                timeframe=trade_details[3],
                entry=trade_details[4],
                SL=trade_details[5],
            )


def test_init_clist():
    """This test checks the init_clist function"""
    td = Trade(
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
        clist=clO_pickled
    )
    newclist = t.clist
    newclist.calc_rsi()
    t.clist = newclist
    assert entry_onrsi == t.is_entry_onrsi()
'''
@pytest.mark.parametrize(
    "start,type,SL,TP,entry,outcome,pips",
    [
        ("2017-05-10 21:00:00", "long", 0.73176, 0.75323, 0.73953, "success", 137.0),
        ("2017-06-08 21:00:00", "short", 0.75715, 0.74594, 0.75255, "failure", -45.0),
        ("2023-01-10 21:00:00", "short", 0.70655, 0.66787, 0.68875, "failure", -179),
    ],
)
def test_run_trade(start, type, SL, TP, entry, outcome, pips, clO_pickled):
    """This test checks the progression of the Trade and checks if the outcome
    attribute is correctly defined."""

    td = Trade(
        start=start,
        entry=entry,
        SL=SL,
        TP=TP,
        pair="AUD_USD",
        type=type,
        timeframe="D",
        clist=clO_pickled,
    )
    td.run_trade()
    assert td.outcome == outcome
    assert td.pips == pips


def test_run_single_trade(clO_pickled):
    """This test checks the progression of the Trade and checks
    if several Trade attributes are correctly defined."""
    td = Trade(
        start="2017-05-10 21:00:00",
        entry=0.73953,
        SL=0.73176,
        TP=0.75323,
        pair="AUD_USD",
        type="long",
        timeframe="D",
        clist=clO_pickled,
        clist_tm=clO_pickled,
    )
    td.run_trade()
    td.start == "2017-05-10 21:00:00"
    td.entry_time == "2017-05-11T21:00:00"
    td.outcome == "success"
    td.pips == 137.0
    td.end == "2017-06-06 21:00:00"


@pytest.mark.parametrize("pair,start,type,SL,TP,entry,entered", trade_data1)
def test_run_trade_wexpire(pair, start, type, SL, TP, entry, entered, clO_pickled):
    """This test checks the run_trade method with the 'expires' parameter"""
    td = Trade(
        start=start,
        entry=entry,
        SL=SL,
        TP=TP,
        pair=pair,
        type=type,
        timeframe="D",
        clist=clO_pickled,
    )

    td.run_trade(expires=2)
    assert td.entered == entered

def test_run_trade_noclO():
    """Run run_trade without passing a pickled CandeList object"""
    td = Trade(
        start="2017-12-11 22:00:00",
        entry=0.75407,
        SL=0.74790,
        TP=0.77057,
        pair="AUD_USD",
        type="long",
        timeframe="D",
    )
    td.run_trade()

trade_data2 = [
    ("2018-06-21 22:00:00", "long", 0.72948, 0.75621, 0.73873),
    ("2018-06-26 22:00:00", "short", 0.75349, 0.72509, 0.73929),
]

pips2 = [(0.6), (-66.6)]
u_trade_data2 = [(*trade, pip) for trade, pip in zip(trade_data2, pips2)]

@pytest.mark.parametrize("start,type,SL,TP,entry, pips", u_trade_data2)
def test_run_trade_over(start, type, SL, TP, entry, pips, clO_pickled):
    """Run trade over the numperiods limit"""
    trade_params.numperiods = 10
    td = Trade(
        start=start,
        entry=entry,
        SL=SL,
        TP=TP,
        pair="AUD_USD",
        type=type,
        timeframe="D",
        clist=clO_pickled,
    )
    td.run_trade(expires=2)
    assert td.pips == pips
'''