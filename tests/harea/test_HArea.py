import pytest

from apis.oanda_api import OandaAPI
from harea import HArea
from candle.candlelist import CandleList
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

    resist = HArea(price=0.70151,
                   pips=5,
                   instrument='AUD_USD',
                   granularity='D',
                   settingf='data/settings.ini')

    lt = resist.last_time(clist=cl_object.clist, position='above')

    assert lt == datetime.datetime(2019, 7, 21, 21, 0)

@pytest.mark.parametrize("clist_ix, price, dt", [(-1, 0.69718, datetime.datetime(2020, 1, 3, 2, 0)),
                                                 (-2, 0.70023, datetime.datetime(2020, 1, 2, 5, 0)),
                                                 (-3, 0.70513, 'n.a.')])
def test_get_cross_time(cl_object, clist_ix, price, dt):
    '''
    Test 'get_cross_time' function from HArea
    for a single candle that crosses the 'resist' object
    '''

    resist = HArea(price=price,
                   pips=5,
                   instrument='AUD_USD',
                   granularity='D',
                   settingf='data/settings.ini')

    cross_time = resist.get_cross_time(candle=cl_object.clist[clist_ix])

    assert cross_time == dt