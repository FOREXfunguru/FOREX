import pytest
import pdb

from TradeJournal.trade import Trade

@pytest.fixture
def t_object():
    '''Returns a Trade object'''

    td=Trade(
        start="2017-04-20T14:00:00",
        end="2017-04-26T14:00:00",
        pair="AUD/USD",
        type="long",
        timeframe="H8",
        strat="counter_b2",
        id= "AUD_USD 20APR2017H8",
        settingf="data/settings.ini"
        )
    return td

@pytest.fixture
def unfisished_t_object():
    ''' Returns a Trade object without the end defined'''

    td = Trade(
        start="2018-12-12 10:00:00",
        entry=1.57488,
        SL=1.56685,
        TP=1.58724,
        pair="EUR/AUD",
        type="long",
        timeframe="H12",
        strat="counter_b2",
        id="EUR_AUD 12DEC2018H12",
        settingf="data/settings.ini"
    )
    return td

def test_fetch_candlelist(t_object):
    '''
    This test checks the function to return a CandleList object 
    corresponding to this trade
    '''
    
    cl=t_object.fetch_candlelist()
    assert cl.clist[0].openBid==0.7521
    assert cl.clist[0].highBid==0.75464

def test_run_trade(unfisished_t_object):
    '''
    This test checks the progression of the Trade
    and checks if the outcome attribute is correctly
    defined.
    '''

    unfisished_t_object.run_trade()
    assert unfisished_t_object.outcome=='success'

