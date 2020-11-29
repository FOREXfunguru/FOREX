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

    assert '2019-06-17T21:00:00.000000Z' == s_object.get_lowest()['time']

def test_get_highest(s_object):
    '''Test 'get_highest' function'''

    assert '2019-07-03T21:00:00.000000Z' == s_object.get_highest()['time']