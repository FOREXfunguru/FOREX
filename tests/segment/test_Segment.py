from config import CONFIG

import datetime
import pytest
import pdb

@pytest.fixture
def s_object(clO):
    '''Returns Segment object'''

    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots',
                                                      'th_bounces'))

    slist = pl.slist
    return slist.slist[2]

@pytest.fixture
def two_segments(clO):
    '''Returns 2 Segment objects'''

    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots',
                                                      'th_bounces'))

    slist = pl.slist
    return slist.slist[2],slist.slist[3]

def test_get_lowest(s_object):
    '''Test 'get_lowest' function'''

    assert datetime.datetime(2019, 6, 17, 21, 0) == s_object.get_lowest()['time']

def test_get_highest(s_object):
    '''Test 'get_highest' function'''

    assert datetime.datetime(2019, 7, 3, 21, 0) == s_object.get_highest()['time']

def test_append(two_segments):
    '''Test 'append' function'''
    first_s = two_segments[0]
    # count of 1st segment before append
    assert first_s.count == 23
    # diff of 1st segment before append
    assert first_s.diff == 156.5
    second_s = two_segments[1]
    first_s.append(second_s)
    # count of 1st segment after append
    assert first_s.count == 55
    # diff of 1st segment after append
    assert first_s.diff == 111.0

def test_prepend(two_segments):
    '''Test 'prepend' function'''
    first_s = two_segments[0]
    second_s = two_segments[1]
    # count of 2nd segment before append
    assert second_s.count == 32
    # diff of 2nd segment before append
    assert second_s.diff == 333.3
    second_s.prepend(first_s)
    # count of 2nd segment after append
    assert second_s.count == 55
    # diff of 2nd segment after append
    assert second_s.diff == 111.0

