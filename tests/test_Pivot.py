from oanda_api import OandaAPI
from candlelist import CandleList

import pytest
import traceback
import glob
import os
import datetime
import pdb

@pytest.fixture
def cl_object():
    '''Returns CandleList object'''

    oanda = OandaAPI(instrument='AUD_USD',
                     granularity='D',
                     settingf='data/settings.ini')

    oanda.run(start='2015-06-24T22:00:00',
              end='2019-06-21T22:00:00')

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list,
                    instrument='AUD_USD',
                    type='long',
                    settingf='data/settings.ini')
    return cl

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('data/tmp/*')
    for f in files:
        os.remove(f)

def test_pre_aft_lens(cl_object):
    '''
    Check if 'pre' and 'aft' Segments have the
    correct number of candles
    '''

    pl = cl_object.get_pivotlist()

    pivot = pl.plist[3]

    assert len(pivot.pre.clist) == 20
    assert len(pivot.aft.clist) == 8

def test_pre_aft_start(cl_object):
    '''
    Check if 'pre' and 'aft' Segments have the
    correct start Datetimes
    '''

    pl = cl_object.get_pivotlist()

    pivot = pl.plist[3]

    assert datetime.datetime(2015, 8, 6, 21, 0) == pivot.pre.start()
    assert datetime.datetime(2015, 9, 3, 21, 0) == pivot.aft.start()

def test_merge_pre(cl_object):
    '''
    Test function 'merge_pre' to merge the 'pre' Segment
    '''
    pl = cl_object.get_pivotlist()

    pivot = pl.plist[3]
    # Check pivot.pre.start() before running 'merge_pre'
    assert datetime.datetime(2015, 8, 6, 21, 0) == pivot.pre.start()

    # run 'merge_pre' function
    pivot.merge_pre(slist=pl.slist)

    # Check pivot.pre.start() after running 'merge_pre'

    assert datetime.datetime(2015, 6, 24, 21, 0) == pivot.pre.start()
"""
def test_merge_aft(cl_object):
    '''
    Test function to merge 'aft' Segment
    '''
    pl = cl_object.get_pivotlist(outfile='data/tmp/test.png',
                                 th_up=0.01, th_down=-0.01)

    adt = datetime.datetime(2015, 8, 16, 21, 0)

    rpt = pl.fetch_by_time(adt)

    rpt.merge_aft(slist=pl.slist, n_candles=5)

    assert datetime.datetime(2015, 9, 6, 21, 0)== rpt.aft.end()

def test_calc_score(cl_object, clean_tmp):
    '''
    Test function named 'calc_score'
    '''
    pl = cl_object.get_pivotlist(outfile='data/tmp/test.png',
                                 th_up=0.01, th_down=-0.01)

    adt = datetime.datetime(2015, 8, 16, 21, 0)

    rpt = pl.fetch_by_time(adt)

    score=rpt.calc_score()

    assert score==19
"""