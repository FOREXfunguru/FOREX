import pytest

from trading_journal.open_trade import UnawareTrade

from data_for_tests import (trades1,
                            trades_entered,
                            trades_outcome)

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


trade_data1 = [(*trade, pip) for trade, pip in zip(trades_entered, trades_outcome)]

@pytest.mark.parametrize("start,type,SR,SL,TP,entry,trades_outcome", trade_data1)
def test_run(start, type, SR, SL, TP, entry, trades_outcome, clOH8_2019_pickled, clO_pickled):
    """Test 'run' function"""
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
        clist_tm=clO_pickled,
        connect=False)
    t.initialise()
    t.run()
    assert t.outcome == trades_outcome[0]
    assert t.pips == trades_outcome[1]

