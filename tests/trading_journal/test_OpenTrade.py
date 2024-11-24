import pytest
import datetime

from trading_journal.open_trade import (
    OpenTrade,
    BreakEvenTrade,
    AwareTrade,
    UnawareTrade,
    TrackingTrade,
    TrackingAwareTrade
)
from trading_journal.trade_utils import check_timeframes_fractions
from data_for_tests import trades1, trades_entered, trades_for_test_run
from params import trade_management_params


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

    def init_trades(self, mock_trades):
        features = ["start", "pair", "timeframe", "type", "SR", "SL", "entry"]
        trade_features_list = []
        for trade_values in mock_trades:
            trade_features_list.append({key: value for key, value in zip(features,
                                                                         trade_values)})
        return trade_features_list

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
        trade_features_list = self.init_trades(mock_trades=trades_entered)
        td = OpenTrade(
            **trade_features_list[0],
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

    def test_append_trademanagement_candles(self):
        open_trade = OpenTrade(RR=1.5,
                               **self.trade_features,
                               init_clist=True)
        open_trade.append_trademanagement_candles(d=datetime.datetime(2023, 1, 10, 21, 0, 0),
                                                  fraction=3)
        expected_hours = [22, 6, 14]
        for i, expected_hour in enumerate(expected_hours):
            assert (
                open_trade.preceding_candles[i].time.hour == expected_hour
            ), f"Expected hour {expected_hour}, but got {open_trade.preceding_candles[i].time.hour}"

    @pytest.mark.parametrize(
        "trade_feats, results",
        [
            (("D", "H8", (datetime.datetime(2023, 1, 10, 21, 0, 0))), (0, 0.7081)),
            (("H12", "H8", (datetime.datetime(2023, 1, 10, 21, 0, 0))), (2, 0.7081)),
            (("H12", "H8", (datetime.datetime(2023, 1, 10, 9, 0, 0))), (2, 0.7081))
        ],
    )
    def test_process_trademanagement(self, trade_feats, results):
        """Tests process_trademanagent which is also invoking 'check_timeframes_fractions'
        to calculate the fraction of candles
        """
        fraction = check_timeframes_fractions(timeframe1=trade_feats[0],
                                              timeframe2=trade_feats[1])
        open_trade = OpenTrade(RR=1.5,
                               **self.trade_features,
                               init_clist=True)
        open_trade.process_trademanagement(d=trade_feats[2],
                                           fraction=fraction)
        assert len(open_trade.preceding_candles) == results[0]
        assert open_trade.SL.price == results[1]


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
        trade_features_list = self.init_trades(mock_trades=trades_entered)
        if exp_instance is BreakEvenTrade:
            BreakEvenTrade(
                RR=RR, TP=TP, **trade_features_list[0], init_clist=False
            )
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                BreakEvenTrade(
                    RR=RR, TP=TP, **trade_features_list[0],
                    init_clist=False
                )

    def test_run(self, clOH8_2019_pickled, clO_pickled):
        trade_features_list = self.init_trades(mock_trades=trades_entered)
        for ix in range(len(trade_features_list)):
            breakeven_trade_object = BreakEvenTrade(
                **trade_features_list[ix],
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
        trade_features_list = self.init_trades(mock_trades=trades_entered)
        for ix in range(len(trade_features_list)):
            aware_trade_object = AwareTrade(
                **trade_features_list[ix],
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

    # trades outcome for test_run() function
    trades_outcome = [
         ("success", 114.0),  # outcome , pips
         ("failure", 18),
         ("failure", -24.0),
         ("failure", -40.0),
    ]

    # trades outcome for test_run1() function
    trades_outcome1 = [
         ("n.a.", -15.6),  # outcome , pips
         ("n.a.", -15.6),
         ("n.a.", 39)
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
        trade_features_list = self.init_trades(mock_trades=trades_entered)
        if exp_instance is UnawareTrade:
            UnawareTrade(RR=RR, TP=TP, **trade_features_list[0],
                         init_clist=False)
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                UnawareTrade(
                    RR=RR, TP=TP, **self.trade_features_list[0],
                    init_clist=False
                )

    def test_run(self, clOH8_2019_pickled, clO_pickled):
        trade_features_list = self.init_trades(mock_trades=trades_entered)
        for ix in range(len(trade_features_list)):
            unaware_trade_object = UnawareTrade(
                **trade_features_list[ix],
                RR=1.5,
                clist=clO_pickled,
                clist_tm=clOH8_2019_pickled,
                connect=False,
            )
            unaware_trade_object.initialise()
            unaware_trade_object.run()
            assert unaware_trade_object.outcome == self.trades_outcome[ix][0]
            assert unaware_trade_object.pips == self.trades_outcome[ix][1]

    def test_run1(self):
        """Test run() with different timeframes and start of the trades.
        Just to check how well the method behaves, also this test will not
        used the pickled clists
        """
        trade_management_params.numperiods = 5
        trade_features_list = self.init_trades(mock_trades=trades_for_test_run)
        for ix in range(len(trade_features_list)):
            unaware_trade_object = UnawareTrade(
                **trade_features_list[ix],
                RR=1.5,
                init_clist=True
            )
            unaware_trade_object.initialise()
            unaware_trade_object.run()
            assert unaware_trade_object.outcome == self.trades_outcome1[ix][0]
            assert unaware_trade_object.pips == self.trades_outcome1[ix][1]


class TestTrackingTrade(TestOpenTrade):

    # trades outcome for run() function
    trades_outcome = [
        ("success", 114.0, datetime.datetime(2019, 4, 23, 21, 0)),  # outcome , pips, end datetime
        ("failure", 9.0, datetime.datetime(2019, 5, 30, 21, 0)),
        ("failure", -56.0, datetime.datetime(2019, 7, 23, 21, 0)),
        ("failure", -81.0, datetime.datetime(2019, 9, 2, 21, 0)),
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
        trade_features_list = self.init_trades(mock_trades=trades_entered)
        if exp_instance is TrackingTrade:
            TrackingTrade(RR=RR, TP=TP, **trade_features_list[0],
                          init_clist=False)
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                TrackingTrade(
                    RR=RR, TP=TP, **trade_features_list[0],
                    init_clist=False
                )

    def test_run(self, clOH8_2019_pickled, clO_pickled):
        trade_features_list = self.init_trades(mock_trades=trades_entered)
        for ix in range(len(trade_features_list)):
            tracking_trade_object = TrackingTrade(
                **trade_features_list[ix],
                RR=1.5,
                clist=clO_pickled,
                clist_tm=clOH8_2019_pickled,
                connect=False,
            )
            tracking_trade_object.initialise()
            tracking_trade_object.run()
            assert tracking_trade_object.outcome == self.trades_outcome[ix][0]
            assert tracking_trade_object.pips == self.trades_outcome[ix][1]
            assert tracking_trade_object.end == self.trades_outcome[ix][2]


class TestTrackingAwareTrade(TestOpenTrade):

    # trades outcome for run() function
    trades_outcome = [
        ("success", 114.0, datetime.datetime(2019, 4, 23, 21, 0)),  # outcome , pips, end datetime
        ("failure", 9.0, datetime.datetime(2019, 5, 30, 21, 0)),
        ("failure", -141.0, datetime.datetime(2019, 7, 25, 21, 0)),
        ("failure", 72.0, datetime.datetime(2019, 9, 16, 21, 0)),
    ]

    @pytest.mark.parametrize(
        "TP, RR, exp_instance",
        [
            (0.86032, None, TrackingAwareTrade),
            (None, 1.5, TrackingAwareTrade),
            (None, None, Exception),
        ],
    )
    def test_instantiation(self, TP, RR, exp_instance):
        trade_features_list = self.init_trades(mock_trades=trades_entered)
        if exp_instance is TrackingAwareTrade:
            TrackingAwareTrade(RR=RR, TP=TP, **trade_features_list[0],
                               init_clist=False)
        elif exp_instance == Exception:
            with pytest.raises(Exception):
                TrackingAwareTrade(
                    RR=RR, TP=TP, **trade_features_list[0],
                    init_clist=False
                )

    def test_run(self, clOH8_2019_pickled, clO_pickled):
        trade_features_list = self.init_trades(mock_trades=trades_entered)
        for ix in range(len(trade_features_list)):
            tracking_aware_trade_object = TrackingAwareTrade(
                **trade_features_list[ix],
                RR=1.5,
                clist=clO_pickled,
                clist_tm=clOH8_2019_pickled,
                connect=False,
            )
            tracking_aware_trade_object.initialise()
            tracking_aware_trade_object.run()
            assert tracking_aware_trade_object.outcome == self.trades_outcome[ix][0]
            assert tracking_aware_trade_object.pips == self.trades_outcome[ix][1]
            assert tracking_aware_trade_object.end == self.trades_outcome[ix][2]
