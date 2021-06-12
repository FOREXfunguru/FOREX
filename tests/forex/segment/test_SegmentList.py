from config import CONFIG

import datetime
import pytest

@pytest.fixture
def pl_object(clO):
    '''Returns PivotList object'''

    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots',
                                                      'th_bounces'))

    return pl

def test_calc_diff(pl_object):
    """Function to test the 'calc_diff' function"""

    slist = pl_object.slist
    slist.calc_diff()

    #when diff is + it means that
    #the Segment is in a downtrend
    assert slist.diff == 167.3

def test_length_of_segment(pl_object):
    """Test the length function of Segment"""

    slist = pl_object.slist

    assert slist.slist[0].length() == 29

def test_length_of_segmentlist(pl_object):
    """Test the length function of SegmentList"""

    slist = pl_object.slist

    assert slist.length() == 229

def test_start(pl_object):
    """Test start"""

    slist = pl_object.slist

    assert slist.start() == datetime.datetime(2019, 3, 6, 22, 0)

def test_end(pl_object):
    """Test end function"""

    slist = pl_object.slist

    assert slist.end() == datetime.datetime(2020, 1, 22, 22, 0)

def test_fetch_by_start(pl_object):
    """Test fetch_by_start"""

    slist = pl_object.slist

    adt = datetime.datetime(2019, 4, 16, 21, 0)
    s = slist.fetch_by_start(adt)

    assert s.start() == adt

def test_fetch_by_end(pl_object):
    """Test fetch_by_end"""

    slist = pl_object.slist

    adt = datetime.datetime(2019, 6, 13, 21, 0)

    s = slist.fetch_by_end(adt)

    assert s.end() == adt
