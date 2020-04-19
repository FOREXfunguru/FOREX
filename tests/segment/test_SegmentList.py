from apis.oanda_api import OandaAPI
from candle.candlelist import CandleList

import datetime

import pytest


@pytest.fixture
def pl_object():
    '''Returns PivotList object'''

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

    return pl

def test_calc_diff(pl_object):
    """Function to test the 'calc_diff' function"""

    slist = pl_object.slist
    slist.calc_diff()

    #when diff is + it means that
    #the Segment is in a downtrend
    assert slist.diff == 262.9

def test_length_of_segment(pl_object):
    """Test the length function of Segment"""

    slist = pl_object.slist

    assert slist.slist[0].length() == 27

def test_length_of_segmentlist(pl_object):
    """Test the length function of SegmentList"""

    slist = pl_object.slist

    assert slist.length() == 109

def test_start(pl_object):
    """Test start"""

    slist = pl_object.slist

    assert slist.start() == datetime.datetime(2019, 3, 10, 21, 0)

def test_end(pl_object):
    """Test end function"""

    slist = pl_object.slist

    assert slist.end() == datetime.datetime(2019, 8, 7, 21, 0)

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
