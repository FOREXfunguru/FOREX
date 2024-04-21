import pytest
import pdb
from trading_journal.open_trade import OpenTrade, BreakEvenTrade, AwareTrade
from data_for_tests import trades1, trades_entered


class TestOpenTrade:
    trade_features= {
        "start":"2016-12-28 22:00:00",
        "pair":"AUD_USD",
        "timeframe":"D",
        "type": "short",
        "SR": 0.71857,
        "SL":0.70814,
        "entry":0.72193,
    }
    trade_features_list = []
    features = ["start", "pair", "timeframe", "type", "SR", "SL", "entry"]
    for trade_values in trades_entered:
        trade_features_list.append({key: value for key, value in zip(features, trade_values)})
    
    @pytest.mark.parametrize(
    "TP, RR, exp_instance",
    [(0.86032, None, OpenTrade), (None, 1.5, OpenTrade), (None, None, Exception)],
    )
    def test_instantiation(self, TP, RR, exp_instance):
        if exp_instance is OpenTrade:
            OpenTrade(
                RR=RR,
                TP=TP,
                **self.trade_features,
                init_clist=False
            )
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                OpenTrade(
                    RR=RR,
                    TP=TP,
                    **self.trade_features,
                    init_clist=False
                )

    def test_init_clist(self):
        td = OpenTrade(
            **self.trade_features_list[0],
            TP=0.74267,
            init_clist=True,
        )   
        assert len(td.clist.candles) == 4141

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
    @pytest.mark.parametrize(
    "TP, RR, exp_instance",
    [(0.86032, None, BreakEvenTrade), (None, 1.5, BreakEvenTrade), (None, None, Exception)],
    )
    def test_instantiation(self, TP, RR, exp_instance):
        if exp_instance is BreakEvenTrade:
            BreakEvenTrade(
                RR=RR,
                TP=TP,
                **self.trade_features_list[0],
                init_clist=False
            )
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                BreakEvenTrade(
                    RR=RR,
                    TP=TP,
                    **self.trade_features_list[0],
                    init_clist=False
                )
class TestAwareTrade(TestOpenTrade):

    # trades outcome for run() function
    trades_outcome = [
    ("success", 114.0), # outcome , pips
    ]

    @pytest.mark.parametrize(
    "TP, RR, exp_instance",
    [(0.86032, None, AwareTrade), (None, 1.5, AwareTrade), (None, None, Exception)],
    )
    def test_instantiation(self, TP, RR, exp_instance):
        if exp_instance is AwareTrade:
            AwareTrade(
                RR=RR,
                TP=TP,
                **self.trade_features_list[0],
                init_clist=False
            )
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                AwareTrade(
                    RR=RR,
                    TP=TP,
                    **self.trade_features_list[0],
                    init_clist=False
                )

    def test_run(self, clOH8_2019_pickled, clO_pickled):
        for ix in range(len(self.trade_features_list)):
            aware_trade_object = AwareTrade(
                **self.trade_features_list[ix],
                RR=1.5,
                clist=clO_pickled,
                clist_tm=clOH8_2019_pickled,
                connect=False,
            )
            aware_trade_object.initialise()
            aware_trade_object.run()
            aware_trade_object.outcome == self.trades_outcome[ix][0]
            aware_trade_object.pips == self.trades_outcome[ix][1]
