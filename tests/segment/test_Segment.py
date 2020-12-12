from config import CONFIG

import datetime
import pytest

@pytest.fixture
def s_object(clO):
    '''Returns Segment object'''

    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots',
                                                      'th_bounces'))

    slist = pl.slist
    return slist.slist[2]

def test_get_lowest(s_object):
    '''Test 'get_lowest' function'''

    assert datetime.datetime(2019, 6, 17, 21, 0) == s_object.get_lowest()['time']

def test_get_highest(s_object):
    '''Test 'get_highest' function'''

    assert datetime.datetime(2019, 7, 3, 21, 0) == s_object.get_highest()['time']