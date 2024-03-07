import pytest
from trading_journal.open_trade import OpenTrade
from data_for_tests import trades1


def test_instantiation():
    open_trade = OpenTrade(
        start="2016-12-28 22:00:00",
        pair="AUD_USD",
        timeframe="D",
        type=type,
        SR=0.71857,
        SL=0.70814,
        TP=0.74267,
        entry=0.72193,
        init_clist=False
    )
    assert isinstance(open_trade, OpenTrade)

results = [True, False, True, False]
prices = [0.72632, 0.74277, 0.79, 0.74]
trade_data1 = [(*trade, price) for trade, price in zip(trades1, prices)]
trade_data2 = [(*trade, result) for trade, result in zip(trade_data1, results)]

@pytest.mark.parametrize("start,type,SR,SL,TP,entry,price,result", trade_data2)
def test_isin_profit(start, type, SR, SL, TP, entry, price, result):
    open_trade = OpenTrade(
        start=start,
        pair="AUD_USD",
        timeframe="D",
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        init_clist=False)
    assert open_trade.isin_profit(price=price) is result
