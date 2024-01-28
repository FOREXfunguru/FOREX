import pytest

from trading_journal.open_trade import Trade, AwareTrade
from forex.candle import Candle

from data_for_tests import (trades1,
                            trades_entered,
                            trades_outcome1)

trade_details = ["2020-02-19T21:00:00", "EUR_GBP", "long", "D", 0.83585, 0.82467]

@pytest.mark.parametrize(
    "TP, RR, exp_instance",
    [(0.86032, None, AwareTrade), (None, 1.5, AwareTrade), (None, None, Exception)],
)
def test_instantiation(TP, RR, exp_instance):
    if exp_instance is AwareTrade:
        AwareTrade(
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
            AwareTrade(
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
    td = AwareTrade(
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


trade_data1 = [(*trade, pip) for trade, pip in zip(trades_entered, trades_outcome1)]

@pytest.mark.parametrize("start,type,SR,SL,TP,entry,trades_outcome", trade_data1)
def test_run(start, type, SR, SL, TP, entry, trades_outcome, clOH8_2019_pickled, clO_pickled):
    """Test 'run' function"""
    t = AwareTrade(
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

