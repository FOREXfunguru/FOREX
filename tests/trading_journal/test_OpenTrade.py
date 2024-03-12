import pytest
import pdb
from trading_journal.open_trade import OpenTrade, BreakEvenTrade
from data_for_tests import trades1



class TestOpenTrade:
    trade_features= {
        "start":"2016-12-28 22:00:00",
        "pair":"AUD_USD",
        "timeframe":"D",
        "type": "short",
        "SR": 0.71857,
        "SL":0.70814,
        "TP":0.74267,
        "entry":0.72193,
    }
    def test_instantiation(self):
        open_trade = OpenTrade(
            start=self.trade_features["start"],
            pair=self.trade_features["pair"],
            timeframe=self.trade_features["timeframe"],
            type=self.trade_features["type"],
            SR=self.trade_features["SR"],
            SL=self.trade_features["SL"],
            TP=self.trade_features["SL"],
            entry=self.trade_features["entry"],
            init_clist=False
        )
        assert isinstance(open_trade, OpenTrade)

    results = [True, False, True, False]
    prices = [0.72632, 0.74277, 0.79, 0.74]
    trade_data1 = [(*trade, price) for trade, price in zip(trades1, prices)]
    trade_data2 = [(*trade, result) for trade, result in zip(trade_data1, results)]
    @pytest.mark.parametrize("start,type,SR,SL,TP,entry,price,result", trade_data2)
    def test_isin_profit(self, start, type, SR, SL, TP, entry, price, result):
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


class TestBreakEvenTrade(TestOpenTrade):
    def test_instantiation(self):
        bkeven_trade = BreakEvenTrade(
            start=self.trade_features["start"],
            pair=self.trade_features["pair"],
            timeframe=self.trade_features["timeframe"],
            type=self.trade_features["type"],
            SR=self.trade_features["SR"],
            SL=self.trade_features["SL"],
            TP=self.trade_features["SL"],
            entry=self.trade_features["entry"],
            init_clist=False
        )
        assert isinstance(open_trade, BreakEvenTrade)
    
    def test_run(self, clO_pickled, clOH8_2019_pickled):
        bkeven_trade = BreakEvenTrade(
            start=self.trade_features["start"],
            pair=self.trade_features["pair"],
            timeframe=self.trade_features["timeframe"],
            type=self.trade_features["type"],
            SR=self.trade_features["SR"],
            SL=self.trade_features["SL"],
            TP=self.trade_features["SL"],
            entry=self.trade_features["entry"],
            clist=clO_pickled,
            clist_tm=clOH8_2019_pickled
        )
        pdb.set_trace()
        print("h")
        
        
