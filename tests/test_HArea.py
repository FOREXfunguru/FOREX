import pytest
import pdb

from oanda_api import OandaAPI
from harea import HArea
from candlelist import CandleList
import datetime

@pytest.fixture
def oanda_object():
    '''Returns an  oanda object'''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='EUR_AUD',
                     granularity='D',
                     dailyAlignment=22,
                     alignmentTimezone='Europe/London')

    oanda.run(start='2015-08-26T22:00:00',
              end='2016-08-15T22:00:00')

    return oanda


def test_last_time(oanda_object):
    '''
    Test 'last_time' function from HArea
    '''

    candle_list = oanda_object.fetch_candleset()

    cl = CandleList(candle_list, instrument='EUR_AUD', granularity='D')

    resist = HArea(price=0.92216, pips=50, instrument='EUR_AUD', granularity='D')

    lt=resist.last_time(clist=cl.clist, position='above')

    assert lt == datetime.datetime(2016, 8, 15, 21, 0)

def test_get_cross_time(oanda_object):
    '''
    Test 'get_cross_time' function from HArea
    for a single candle that crosses the 'resist' object
    that is centered at 1.57854
    '''

    candle_list = oanda_object.fetch_candleset()

    resist = HArea(price=1.57854, pips=50, instrument='EUR_AUD', granularity='D')

    # Candle that will be analysed for crossing is 27/08/2015
    # which crosses 'resist'
    cross_time = resist.get_cross_time(candle=candle_list[0])

    assert cross_time == datetime.datetime(2015, 8, 27, 9, 0)

def test_get_cross_time1(oanda_object):
    '''
    Test 'get_cross_time' function from HArea
    for a single candle that does not cross the 'resist' object
    that is centered at 1.52287
    '''

    candle_list = oanda_object.fetch_candleset()

    resist = HArea(price=1.52287, pips=50, instrument='EUR_AUD', granularity='D')

    # Candle that will be analysed for crossing is 27/08/2015
    # which does not cross 'resist'
    cross_time = resist.get_cross_time(candle=candle_list[0])

    assert cross_time == "n.a."


def test_get_cross_time2():
    '''
    Test 'get_cross_time' function from HArea
    for a single candle that does not cross the 'resist' object
    that is centered at 0.66662
    '''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='EUR_GBP',
                     granularity='D',
                     dailyAlignment=22,
                     alignmentTimezone='Europe/London')

    oanda.run(start='2004-03-11T22:00:00',
              end='2004-03-23T22:00:00')

    candle_list = oanda.fetch_candleset()

    # Candle that will be analysed for crossing is 22/03/2004
    resist = HArea(price=0.66662, pips=50, instrument='EUR_GBP', granularity='D')

    cross_time = resist.get_cross_time(candle=candle_list[9])


    assert 0==1

