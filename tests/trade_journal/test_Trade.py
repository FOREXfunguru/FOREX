import pytest

from trade_journal.trade import Trade
from apis.ser_data_obj import ser_data_obj


@pytest.fixture
def t_object():
    '''Returns a Trade object'''

    td = Trade(
         start="2017-04-20 14:00:00",
         end="2017-04-26 14:00:00",
         entry=0.75308,
         TP=0.7594,
         SL=0.74889,
         pair="AUD/USD",
         type="long",
         timeframe="H8",
         strat="counter_b2",
         id="AUD_USD 20APR2017H8",
         settingf="../../data/settings.ini"
         )
    return td

def test_t_object_noTP():
    '''Test the instantiation without TP and defined RR'''
    td = Trade(
        start="2017-04-20 14:00:00",
        end="2017-04-26 14:00:00",
        entry=0.75308,
        SL=0.74889,
        RR=1.5,
        pair="AUD/USD",
        type="long",
        timeframe="H8",
        strat="counter_b2",
        id="AUD_USD 20APR2017H8",
        settingf="../../data/settings.ini"
    )

    # check that td.TP has been calculated
    assert td.TP == 0.7594

def test_fetch_candlelist(t_object):
    '''
    This test checks the function to return a CandleList object 
    corresponding to this trade
    '''
    
    cl = t_object.fetch_candlelist()
    assert cl.clist[0].openBid == 0.7521
    assert cl.clist[0].highBid == 0.75464

@pytest.mark.parametrize("pair,start,type,SL,TP,entry, outcome", [
        ('NZD/JPY', '2019-03-22 21:00:00', 'short', 76.797, 73.577, 75.509, 'success'),
        ('AUD/CAD', '2009-10-27 21:00:00', 'short', 0.98435, 0.9564, 0.97316, 'failure'),
        ('EUR/GBP', '2009-09-21 21:00:00', 'short', 0.90785, 0.8987, 0.90421, 'failure'),
        ('EUR/GBP', '2010-02-06 22:00:00', 'long', 0.86036, 0.8977, 0.87528, 'success'),
        ('EUR/AUD', '2018-12-03 22:00:00', 'long', 1.53398, 1.55752, 1.54334, 'success'),
        ('EUR/AUD', '2018-09-11 22:00:00', 'short', 1.63633, 1.60202, 1.62763, 'success'),
        ('EUR/AUD', '2017-05-05 22:00:00', 'short', 1.49191, 1.46223, 1.48004, 'failure'),
        ('EUR/AUD', '2019-05-23 22:00:00', 'short', 1.62682, 1.60294, 1.61739, 'failure')
])
def test_run_trade(pair, start, type, SL, TP, entry, outcome):
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
            strat="counter_b2",
            id="test",
            settingf="../../data/settings.ini"
    )

    td.run_trade()
    assert td.outcome == outcome

@pytest.mark.parametrize("pair,start,type,SL,TP,entry,entered", [('EUR/GBP', '2017-03-14 22:00:00', 'short', 0.87885,
                                                                  0.8487, 0.86677, True),
                                                                 ('EUR/GBP', '2016-10-05 22:00:00', 'short', 0.8848,
                                                                  0.86483, 0.87691, False),
                                                                 ('EUR/AUD', '2018-12-03 22:00:00', 'long', 1.53398,
                                                                 1.55752, 1.54334, True)])
def test_run_trade_wexpire(pair, start, type, SL, TP, entry, entered):
    '''
    This test checks the run_trade method with the 'expires' parameter
    '''
    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair=pair,
            type=type,
            timeframe="D",
            strat="counter_b2",
            id="test",
            settingf="../../data/settings.ini"
    )

    td.run_trade(expires=2)
    assert td.entered == entered

@pytest.mark.parametrize("pair,start,type,SL,TP,entry,entered", [('EUR/GBP', '2020-04-21 17:00:00', 'long', 0.88209,
                                                                  0.89279, 0.88636, False)])
def test_run_trade_wexpire_4hrs(pair, start, type, SL, TP, entry, entered):
    '''
    This test checks the run_trade method with the 'expires' parameter
    '''
    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair=pair,
            type=type,
            timeframe="H4",
            strat="counter_b2",
            id="test",
            settingf="../../data/settings.ini"
    )

    td.run_trade(expires=2)
    assert td.entered == entered

@pytest.mark.parametrize("pair,start,type,SL,TP,entry,outcome", [('EUR/GBP', '2019-05-06 01:00:00', 'long', 0.84881,
                                                                  0.85682, 0.85121, 'success'),
                                                                 ('EUR/GBP', '2020-03-25 13:00:00', 'long', 0.90494,
                                                                  0.93197, 0.91553, 'failure')])
def test_run_trade_4hrs(pair, start, type, SL, TP, entry, outcome):
    '''
    This test checks the run_trade method with the 'expires' parameter
    '''
    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair=pair,
            type=type,
            timeframe="H4",
            strat="counter_b2",
            id="test",
            settingf="../../data/settings.ini"
    )

    td.run_trade()
    assert td.outcome == outcome

def test_get_SLdiff(t_object):

    assert 41.9 == t_object.get_SLdiff()