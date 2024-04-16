import pytest

from trading_journal.open_trade import AwareTrade
from data_for_tests import (trades_entered,
                            trades_outcome1)

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

