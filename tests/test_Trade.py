import pytest
import pdb

from TradeJournal.Trade import Trade

@pytest.fixture
def t_object():
    '''Returns a Trade object'''

    td=Trade(
        start="2017-04-20T14:30:00",
        end="2017-04-26T16:43:00",
        pair="AUD/USD",
        type="bullish",
        timeframe="H8"
        )
    return td

@pytest.fixture
def unfisished_t_object():
    ''' Returns a Trade object without the end defined'''
    td = Trade(
        start="2017-04-20T14:30:00",
        pair="AUD/USD",
        type="bullish",
        timeframe="D"
    )
    return td

"""
def test_fetch_candlelist(t_object):
    '''
    This test checks the function to return a CandleList object 
    corresponding to this trade
    '''
    
    cl=t_object.fetch_candlelist()
    assert cl.next().openBid==0.7521
    assert cl.next().highBid==0.75326
"""

def test_run_trade(unfisished_t_object):
    '''
    This test checks the progression of the Trade
    and defines the outcome attribute
    '''

    unfisished_t_object.run_trade()


