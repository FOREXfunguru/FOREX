import pytest
import pdb

from oanda_api import OandaAPI
from harea import HArea
from candlelist import CandleList
import datetime

@pytest.fixture
def cl_object():
    '''Returns a CandleList object'''

    oanda = OandaAPI(
                     instrument='AUD_USD',
                     granularity='D',
                     settingf='data/settings.ini')

    oanda.run(start='2019-03-06T23:00:00',
              end='2020-01-03T23:00:00')

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list,
                    instrument='AUD_USD',
                    granularity='D',
                    settingf='data/settings.ini')
    return cl

def test_last_time(cl_object):
    '''
    Test 'last_time' function from HArea
    '''

    resist = HArea(price=1.44280,
                   instrument='EUR_AUD',
                   granularity='D',
                   settingf='data/settings.ini')

    lt = resist.last_time(clist=cl_object.clist, position='below')

    assert lt == datetime.datetime(2015, 6, 1, 21, 0)

def test_get_cross_time(cl_object):
    '''
    Test 'get_cross_time' function from HArea
    for a single candle that crosses the 'resist' object
    that is centered at 1.57854
    '''

    resist = HArea(price=1.46341,
                   instrument='EUR_AUD',
                   granularity='D',
                   settingf='data/settings.ini')

    # Candle that will be analysed for crossing is 4/08/2016
    # which crosses 'resist'
    pdb.set_trace()
    cross_time = resist.get_cross_time(candle=cl_object.clist[-8])

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
