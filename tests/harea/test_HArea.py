import pytest

from oanda.connect import Connect
from harea import HArea
from candle.candlelist import CandleList
import datetime

def test_last_time(clO):
    '''
    Test 'last_time' function from HArea
    '''

    resist = HArea(price=0.70151,
                   pips=5,
                   instrument='AUD_USD',
                   granularity='D')

    lt = resist.last_time(clist=clO.clist, position='above')

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
                   settingf='../../data/settings.ini')

    cross_time = resist.get_cross_time(candle=cl_object.clist[clist_ix])

    assert cross_time == dt

@pytest.mark.parametrize("clist_ix, price, dt", [(-1, 0.69718, datetime.datetime(2020, 1, 3, 2, 0)),
                                                 (-2, 0.70023, datetime.datetime(2020, 1, 2, 5, 0)),
                                                 (-3, 0.70513, 'n.a.')])
def test_get_cross_time_gran(cl_object, clist_ix, price, dt):
    '''
    Test 'get_cross_time' function from HArea
    for a single candle that crosses the 'resist' object
    '''
    resist = HArea(price=price,
                   pips=5,
                   instrument='AUD_USD',
                   granularity='D',
                   settingf='../../data/settings.ini')

    cross_time = resist.get_cross_time(candle=cl_object.clist[clist_ix],
                                       granularity='H1')

    assert cross_time == dt