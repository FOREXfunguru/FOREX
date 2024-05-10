import pytest

from trading_journal.open_trade import (
    OpenTrade,
    BreakEvenTrade,
    AwareTrade,
    UnawareTrade,
    TrackingTrade,
)
from data_for_tests import trades1, trades_entered


class TestOpenTrade:
    trade_features = {
        "start": "2016-12-28 22:00:00",
        "pair": "AUD_USD",
        "timeframe": "D",
        "type": "short",
        "SR": 0.71857,
        "SL": 0.70814,
        "entry": 0.72193,
    }
    trade_features_list = []
    features = ["start", "pair", "timeframe", "type", "SR", "SL", "entry"]
    for trade_values in trades_entered:
        trade_features_list.append({key: value for key, value in zip(features,
                                                                     trade_values)})

    @pytest.mark.parametrize(
        "TP, RR, exp_instance",
        [(0.86032, None, OpenTrade), (None, 1.5, OpenTrade), (None, None, Exception)],
    )
    def test_instantiation(self, TP, RR, exp_instance):
        if exp_instance is OpenTrade:
            OpenTrade(RR=RR, TP=TP, **self.trade_features, init_clist=False)
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                OpenTrade(RR=RR, TP=TP, **self.trade_features, init_clist=False)

    def test_init_clist(self):
        td = OpenTrade(
            **self.trade_features_list[0],
            TP=0.74267,
            init_clist=True,
        )
        assert len(td.clist.candles) == 4130

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
            init_clist=False,
        )
        assert open_trade.isin_profit(price=price) is result


class TestBreakEvenTrade(TestOpenTrade):

    # trades outcome for run() function
    trades_outcome = [
        ("success", 114.0),  # outcome, pips
        ("failure", 10),
        ("failure", 10),
        ("failure", 10),
    ]

    @pytest.mark.parametrize(
        "TP, RR, exp_instance",
        [
            (0.86032, None, BreakEvenTrade),
            (None, 1.5, BreakEvenTrade),
            (None, None, Exception),
        ],
    )
    def test_instantiation(self, TP, RR, exp_instance):
        if exp_instance is BreakEvenTrade:
            BreakEvenTrade(
                RR=RR, TP=TP, **self.trade_features_list[0], init_clist=False
            )
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                BreakEvenTrade(
                    RR=RR, TP=TP, **self.trade_features_list[0],
                    init_clist=False
                )

    def test_run(self, clOH8_2019_pickled, clO_pickled):
        for ix in range(len(self.trade_features_list)):
            breakeven_trade_object = BreakEvenTrade(
                **self.trade_features_list[ix],
                RR=1.5,
                clist=clO_pickled,
                clist_tm=clOH8_2019_pickled,
                connect=False,
            )
            breakeven_trade_object.initialise()
            breakeven_trade_object.run()
            assert breakeven_trade_object.outcome == self.trades_outcome[ix][0]
            assert breakeven_trade_object.pips == self.trades_outcome[ix][1]


class TestAwareTrade(TestOpenTrade):

    # trades outcome for run() function
    trades_outcome = [
        ("success", 114.0),  # outcome , pips
        ("failure", 39.0),
        ("failure", -141.0),
        ("n.a.", -7.0),
    ]

    @pytest.mark.parametrize(
        "TP, RR, exp_instance",
        [(0.86032, None, AwareTrade), (None, 1.5, AwareTrade), (None, None, Exception)],
    )
    def test_instantiation(self, TP, RR, exp_instance):
        if exp_instance is AwareTrade:
            AwareTrade(RR=RR, TP=TP, **self.trade_features_list[0], init_clist=False)
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                AwareTrade(
                    RR=RR, TP=TP, **self.trade_features_list[0], init_clist=False
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
            assert aware_trade_object.outcome == self.trades_outcome[ix][0]
            assert aware_trade_object.pips == self.trades_outcome[ix][1]


class TestUnawareTrade(TestOpenTrade):

    # trades outcome for run() function
    trades_outcome = [
        ("success", 114.0),  # outcome , pips
        ("failure", 39),
        ("failure", -97.0),
        ("failure", -22.0),
    ]

    @pytest.mark.parametrize(
        "TP, RR, exp_instance",
        [
            (0.86032, None, UnawareTrade),
            (None, 1.5, UnawareTrade),
            (None, None, Exception),
        ],
    )
    def test_instantiation(self, TP, RR, exp_instance):
        if exp_instance is UnawareTrade:
            UnawareTrade(RR=RR, TP=TP, **self.trade_features_list[0], init_clist=False)
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                UnawareTrade(
                    RR=RR, TP=TP, **self.trade_features_list[0], init_clist=False
                )

    def test_run(self, clOH8_2019_pickled, clO_pickled):
        for ix in range(len(self.trade_features_list)):
            unaware_trade_object = UnawareTrade(
                **self.trade_features_list[ix],
                RR=1.5,
                clist=clO_pickled,
                clist_tm=clOH8_2019_pickled,
                connect=False,
            )
            unaware_trade_object.initialise()
            unaware_trade_object.run()
            assert unaware_trade_object.outcome == self.trades_outcome[ix][0]
            assert unaware_trade_object.pips == self.trades_outcome[ix][1]


class TestTrackingTrade(TestOpenTrade):

    # trades outcome for run() function
    trades_outcome = [
        ("success", 114.0),  # outcome , pips
        ("failure", 9.0),
        ("failure", -56.0),
        ("failure", -81.0),
    ]

    @pytest.mark.parametrize(
        "TP, RR, exp_instance",
        [
            (0.86032, None, TrackingTrade),
            (None, 1.5, TrackingTrade),
            (None, None, Exception),
        ],
    )
    def test_instantiation(self, TP, RR, exp_instance):
        if exp_instance is TrackingTrade:
            TrackingTrade(RR=RR, TP=TP, **self.trade_features_list[0],
                          init_clist=False)
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                TrackingTrade(
                    RR=RR, TP=TP, **self.trade_features_list[0],
                    init_clist=False
                )

    def test_run(self, clOH8_2019_pickled, clO_pickled):
        for ix in range(len(self.trade_features_list)):
            unaware_trade_object = TrackingTrade(
                **self.trade_features_list[ix],
                RR=1.5,
                clist=clO_pickled,
                clist_tm=clOH8_2019_pickled,
                connect=False,
            )
            unaware_trade_object.initialise()
            unaware_trade_object.run()
            assert unaware_trade_object.outcome == self.trades_outcome[ix][0]
            assert unaware_trade_object.pips == self.trades_outcome[ix][1]
