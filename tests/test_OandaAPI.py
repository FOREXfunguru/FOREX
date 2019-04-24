import pytest
import pdb

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

def test_OandaAPI1():
    '''
    Test a simple query to Oanda's REST API using range of datetime
    '''
    # time must be in a valid datetime format
    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument='AUD_USD',
                   granularity='D',
                   alignmentTimezone='Europe/London',
                   dailyAlignment=22,
                   start='2015-01-25T22:00:00',
                   end='2015-01-26T22:00:00')
    assert 1

def test_OandaAPI2():
    '''
    Test a simple query to Oanda's REST API using range of datetime where start time
    falls on Friday at 22:00:00 (when market has just closed) and code raises an Exception
    '''
    with pytest.raises(Exception):
        oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                       instrument='AUD_USD',
                       granularity='D',
                       alignmentTimezone='Europe/London',
                       dailyAlignment=22,
                       start='2018-11-16T22:00:00',
                       end='2018-11-20T22:00:00')

def test_OandaAPI3():
    '''
    Test a simple query to Oanda's REST API using a H12 timeframe
    '''
    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument='AUD_USD',
                   granularity='H12',
                   alignmentTimezone='Europe/London',
                   dailyAlignment=22,
                   start='2018-11-12T10:00:00',
                   end='2018-11-14T10:00:00')
    assert 1

def test_OandaAPI4():
    '''
    Test a simple query to Oanda's REST API using a H12 timeframe and a
    non conventional time that will raise an Exception
    '''
    with pytest.raises(Exception):
        oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                       instrument='AUD_USD',
                       granularity='H12',
                       alignmentTimezone='Europe/London',
                       dailyAlignment=22,
                       start='2018-11-12T10:00:00',
                       end='2018-11-14T11:00:00')

"""
def test_fetch_candleset(oanda_object):
    '''
    Test how a Candle list is retrieved
    after a simple query to Oanda's REST API

    '''

    candle_list = oanda_object.fetch_candleset()
    assert candle_list[0].highBid == 0.79328
    assert candle_list[0].openBid == 0.7873
    assert candle_list[0].lowBid == 0.7857
    assert candle_list[0].representation == 'bidask'
    assert candle_list[0].lowAsk == 0.786
    assert candle_list[0].complete == True
    assert candle_list[0].openAsk == 0.7889
    assert candle_list[0].highAsk == 0.79345
    assert candle_list[0].highBid == 0.79328
    assert candle_list[0].volume == 11612
    assert candle_list[0].closeBid == 0.79316
    assert candle_list[0].closeAsk == 0.79335
    assert candle_list[0].openBid == 0.7873

def test_fetch_one_candle():
    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='AUD_USD',
                     granularity='D',
                     dailyAlignment=22,
                     alignmentTimezone='Europe/London',
                     start='2015-01-25T22:00:00',
                     count=1)

    candle_list=oanda.fetch_candleset()
    assert candle_list[0].highBid == 0.79329
    assert candle_list[0].openBid == 0.7873
    assert candle_list[0].lowBid == 0.7857
    assert candle_list[0].representation == 'bidask'
    assert candle_list[0].lowAsk == 0.786
    assert candle_list[0].complete == True
    assert candle_list[0].openAsk == 0.7889
"""