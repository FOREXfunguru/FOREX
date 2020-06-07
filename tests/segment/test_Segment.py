from apis.oanda_api import OandaAPI
from candle.candlelist import CandleList

import datetime

import pytest


@pytest.fixture
def s_object():
    '''Returns Segment object'''

    oanda = OandaAPI(instrument='AUD_USD',
                     granularity='D',
                     settingf='../../data/settings.ini')

    oanda.run(start='2019-03-08T22:00:00',
              end='2019-08-09T22:00:00')

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list,
                    instrument='AUD_USD',
                    id='AUD_USD_test',
                    type='long',
                    settingf='../../data/settings.ini')

    pl = cl.get_pivotlist(th_bounces=cl.settings.getfloat('pivots',
                                                          'th_bounces'))

    slist = pl.slist
    return slist.slist[2]

def test_get_lowest(s_object):
    '''Test 'get_lowest' function'''

    assert datetime.datetime(2019, 6, 17, 21) == s_object.get_lowest().time

def test_get_highest(s_object):
    '''Test 'get_highest' function'''

    assert datetime.datetime(2019, 7, 3, 21) == s_object.get_highest().time