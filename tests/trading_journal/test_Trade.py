import pytest

from trading_journal.trade import Trade
from params import trade_params

trade_details = ["2020-02-19T21:00:00",
                 "EUR_GBP",
                 "long",
                 "D",
                 0.83585,
                 0.82467]


@pytest.mark.parametrize("TP, RR, exp_instance", [
    (0.86032, None, Trade),
    (None, 1.5, Trade),
    (None, None, Exception)
])
def test_instantiation(TP, RR, exp_instance):
    if exp_instance is Trade:
        Trade(RR=RR,
              TP=TP,
              start=trade_details[0],
              pair=trade_details[1],
              type=trade_details[2],
              timeframe=trade_details[3],
              entry=trade_details[4],
              SL=trade_details[5])
    elif exp_instance == Exception:
        with pytest.raises(Exception):
            Trade(RR=RR,
                  TP=TP,
                  start=trade_details[0],
                  pair=trade_details[1],
                  type=trade_details[2],
                  timeframe=trade_details[3],
                  entry=trade_details[4],
                  SL=trade_details[5])


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
            init_clist=True)
    assert len(td.clist.candles) == 4104


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
            clist=clO_pickled)
    td.run_trade()
    td.start == "2017-05-10 21:00:00"
    td.entry_time == "2017-05-11T21:00:00"
    td.outcome == "success"
    td.pips == 137.0
    td.end == "2017-06-06 21:00:00"


@pytest.mark.parametrize("start,type,SL,TP,entry,outcome,pips", [
        ("2017-05-10 21:00:00", "long", 0.73176, 0.75323, 0.73953,
         "success", 137.0),
        ("2017-06-08 21:00:00", "short", 0.75715, 0.74594, 0.75255,
         "failure", -45.0),
        ("2023-01-10 21:00:00", "short", 0.70655, 0.66787, 0.68875,
         "failure", -179)])
def test_run_trade(start, type, SL, TP, entry, outcome, pips,
                   clO_pickled):
    """This test checks the progression of the Trade and checks if the outcome 
    attribute is correctly defined."""

    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair='AUD_USD',
            type=type,
            timeframe="D",
            clist=clO_pickled)
    td.run_trade()
    assert td.outcome == outcome
    assert td.pips == pips


trade_data1 = [
    ('AUD_USD', '2017-03-14 22:00:00', 'short', 0.87885, 0.8487, 0.86677,
     False),
    ('EUR_GBP', '2016-10-05 22:00:00', 'short', 0.8848, 0.86483, 0.87691,
     False),
    ('EUR_AUD', '2018-12-03 22:00:00', 'long', 1.53398, 1.55752, 1.54334,
     False)]


@pytest.mark.parametrize("pair,start,type,SL,TP,entry,entered", trade_data1)
def test_run_trade_wexpire(pair, start, type, SL, TP, entry,
                           entered, clO_pickled):
    """This test checks the run_trade method with the 'expires' parameter"""
    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair=pair,
            type=type,
            timeframe="D",
            clist=clO_pickled)

    td.run_trade(expires=2)
    assert td.entered == entered


def test_run_trade_noclO():
    """Run run_trade without passing a pickled CandeList object"""
    td = Trade(
        start='2017-12-11 22:00:00',
        entry=0.75407,
        SL=0.74790,
        TP=0.77057,
        pair='AUD_USD',
        type='long',
        timeframe="D",
        init_clist=True)
    td.run_trade()


trade_data2 = [
    ('2018-06-21 22:00:00', 'long', 0.72948, 0.75621, 0.73873),
    ('2018-06-26 22:00:00', 'short', 0.75349, 0.72509, 0.73929)]

pips1 = [(-92.0), (142.0)]
u_trade_data2 = [(*trade, pip) for trade, pip in zip(trade_data2, pips1)]


@pytest.mark.parametrize("start,type,SL,TP,entry,pips", u_trade_data2)
def test_run_trade_exitearly(start, type, SL, TP, entry, pips,
                             clO_pickled):
    """Run a trade using trade_params.strat==exit_early"""
    trade_params.no_candles = 13
    trade_params.reduce_perc = 25
    td = Trade(
              start=start,
              entry=entry,
              SL=SL,
              TP=TP,
              pair="AUD_USD",
              type=type,
              timeframe="D",
              clist=clO_pickled)
    td.run_trade(expires=2)
    assert td.pips == pips


pips2 = [(0.6), (-66.6)]
u_trade_data3 = [(*trade, pip) for trade, pip in zip(trade_data2, pips2)]


@pytest.mark.parametrize("start,type,SL,TP,entry, pips", u_trade_data3)
def test_run_trade_over(start, type, SL, TP, entry, pips,
                        clO_pickled):
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
              clist=clO_pickled)
    td.run_trade(expires=2)
    assert td.pips == pips


def test_get_SLdiff(t_object):

    assert 24.0 == t_object.get_SLdiff()
