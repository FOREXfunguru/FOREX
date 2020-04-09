import pytest

from trade_journal.trade import Trade

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

@pytest.mark.parametrize("pair,start,type,SL,TP,entry, outcome", [('EUR/GBP','2004-06-01 22:00:00', 'long', 0.6623, 0.67418, 0.66704, 'n.a.'),
                                                                  ('EUR/AUD', '2018-12-03 22:00:00', 'long', 1.53398, 1.55752, 1.54334, 'success'),
                                                                  ('EUR/AUD', '2018-09-11 22:00:00', 'short', 1.63633, 1.60202, 1.62763, 'success'),
                                                                  ('EUR/AUD', '2017-05-05 22:00:00', 'short', 1.49191, 1.46223, 1.48004, 'failure'),
                                                                  ('EUR/AUD', '2019-05-23 22:00:00', 'short', 1.62682, 1.60294, 1.61739, 'failure')])
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

