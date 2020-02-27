import pytest
import pdb

from TradeJournal.trade import Trade

@pytest.fixture
def t_object():
    '''Returns a Trade object'''

    td = Trade(
         start="2017-04-20 14:00:00",
         end="2017-04-26 14:00:00",
         pair="AUD/USD",
         type="long",
         timeframe="H8",
         strat="counter_b2",
         id="AUD_USD 20APR2017H8",
         settingf="data/settings.ini"
         )
    return td

def test_fetch_candlelist(t_object):
    '''
    This test checks the function to return a CandleList object 
    corresponding to this trade
    '''
    
    cl = t_object.fetch_candlelist()
    assert cl.clist[0].openBid == 0.7521
    assert cl.clist[0].highBid == 0.75464

@pytest.mark.parametrize("start,type,SL,TP,entry, outcome", [('2018-12-03 22:00:00','long',1.53398,1.55752,1.54334,'success'),
                                                             ('2018-09-11 22:00:00','short',1.63633,1.60202,1.62763,'success'),
                                                             ('2017-05-05 22:00:00','short',1.49191,1.46223,1.48004,'failure'),
                                                             ('2019-05-23 22:00:00','short',1.62682,1.60294,1.61739,'failure')])
def test_run_trade(start, type, SL, TP, entry, outcome):
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
            pair="EUR/AUD",
            type=type,
            timeframe="D",
            strat="counter_b2",
            id="test",
            settingf="data/settings.ini"
    )

    td.run_trade()
    assert td.outcome == outcome

