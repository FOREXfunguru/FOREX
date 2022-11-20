import pytest
import datetime

from trading_journal.trade import Trade

def test_candlelist_inst(t_object):
    '''
    This test checks that the CandeList has been correctly
    instantiated
    '''
    assert t_object.start == datetime.datetime(2017, 4, 10, 14, 0)
    assert t_object.SL == 0.74718

@pytest.mark.parametrize("pair,start,type,SL,TP,entry, outcome", [
        ('AUD_USD', '2017-05-10 21:00:00', 'long', 0.73176, 0.75323, 0.73953, 'success'),
        ('AUD_USD', '2017-06-08 21:00:00', 'short', 0.75715, 0.74594, 0.75255, 'failure')])
def test_run_trade(pair, start, type, SL, TP, entry, outcome, clO_pickled):
    '''
    This test checks the progression of the Trade
    and checks if the outcome attribute is correctly
    defined.
    '''
    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair=pair,
            type=type,
            timeframe="D",
            clist=clO_pickled)

    td.run_trade()
    assert td.outcome == outcome

@pytest.mark.parametrize("pair,start,type,SL,TP,entry,entered", [('AUD_USD', '2017-03-14 22:00:00', 'short', 0.87885,
                                                                  0.8487, 0.86677, False),
                                                                 ('EUR_GBP', '2016-10-05 22:00:00', 'short', 0.8848,
                                                                  0.86483, 0.87691, False),
                                                                 ('EUR_AUD', '2018-12-03 22:00:00', 'long', 1.53398,
                                                                 1.55752, 1.54334, False)])
def test_run_trade_wexpire(pair, start, type, SL, TP, entry, entered, clO_pickled):
    '''This test checks the run_trade method with the 'expires' parameter'''
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

@pytest.mark.parametrize("pair,start,type,SL,TP,entry,entered", [('EUR_GBP', '2020-04-21 17:00:00', 'long', 0.88209,
                                                                  0.89279, 0.88636, False)])
def test_run_trade_wexpire_4hrs(pair, start, type, SL, TP, entry, entered, clO_pickled):
    '''This test checks the run_trade method with the 'expires' parameter'''
    
    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair=pair,
            type=type,
            timeframe="H4",
            strat="counter_b2",
            clist=clO_pickled
            )

    td.run_trade(expires=2)
    assert td.entered == entered

@pytest.mark.parametrize("pair,start,type,SL,TP,entry,outcome", [('EUR_GBP', '2019-05-06 01:00:00', 'long', 0.84881,
                                                                  0.85682, 0.85121, 'n.a.'),
                                                                 ('EUR_GBP', '2020-03-25 13:00:00', 'long', 0.90494,
                                                                  0.93197, 0.91553, 'n.a.')])
def test_run_trade_4hrs(pair, start, type, SL, TP, entry, outcome, clO_pickled):
    '''This test checks the run_trade method with the 'expires' parameter'''
    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair=pair,
            type=type,
            timeframe="H4",
            strat="counter_b2",
            clist=clO_pickled)

    td.run_trade()
    assert td.outcome == outcome

def test_get_SLdiff(t_object):

    assert 24.2 == t_object.get_SLdiff()