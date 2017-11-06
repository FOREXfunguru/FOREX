import pytest

from OandaAPI import OandaAPI

@pytest.fixture
def oanda_object():
    '''Returns an  oanda object'''
 
    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument='AUD_USD',
                   granularity='D',
                   alignmentTimezone='Europe/London',
                   start='2015-01-25T22:00:00',
                   end='2015-01-26T22:00:00')
    return oanda

def test_OandaAPI():
    '''
    Test a simple query to Oanda's REST API using range of datetime

    '''
    # time must be in a valid datetime format
    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument='AUD_USD',
                   granularity='D',
                   alignmentTimezone='Europe/London',
                   start='2015-01-25T22:00:00',
                   end='2015-01-26T22:00:00')

    assert 1

def test_fetch_candleset(oanda_object):
    '''
    Test how a Candle list is retrieved
    after a simple query to Oanda's REST API

    '''

    candle_list=oanda_object.fetch_candleset()
    assert candle_list[0].highBid==0.79328
    assert candle_list[0].openBid==0.7873
    assert candle_list[0].lowBid==0.7857 
    assert candle_list[0].representation=='bidask' 
    assert candle_list[0].lowAsk==0.786 
    assert candle_list[0].complete==True 
    assert candle_list[0].openAsk==0.7889 
    assert candle_list[0].highAsk==0.79345 
    assert candle_list[0].highBid==0.79328 
    assert candle_list[0].volume==11612 
    assert candle_list[0].closeBid==0.79316 
    assert candle_list[0].closeAsk==0.79335 
    assert candle_list[0].openBid==0.7873

def test_set_candle_features(oanda_object):
    '''
    Test function to set basic candle features based on price
    i.e. self.colour, upper_wick, etc...
    '''

    candle_list=oanda_object.fetch_candleset()
    candle_list[0].set_candle_features()
    
    assert candle_list[0].colour=="green"


