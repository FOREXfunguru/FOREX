from oanda_api import OandaAPI
from candlelist import CandleList

import pytest
import traceback
import glob
import os
import datetime
import pdb

@pytest.fixture
def pv_object():
    '''Returns Pivot object'''

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

    pdb.set_trace()

    pl = cl.get_pivotlist()

    return pl[0]

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('data/tmp/*')
    for f in files:
        os.remove(f)

def test_fetch_by_time(pv_object):
    '''Obtain a Pivot object by datetime'''

    pdb.set_trace()
    adt = datetime.datetime(2016, 2, 2, 22, 0)

    rpt = pv_object.fetch_by_time(adt)

    assert rpt.candle.time == adt
    assert 0
"""
def test_fetch_pre(cl_object):
    '''Obtain the 'pre' Segment'''

    pl = cl_object.get_pivotlist(outfile='data/tmp/test.png',
                                 th_up=0.01, th_down=-0.01)

    adt = datetime.datetime(2015, 8, 16, 21, 0)

    rpt = pl.fetch_by_time(adt)

    assert len(rpt.pre.clist) == 3

def test_merge_pre(cl_object):
    '''
    Test function to merge 'pre' Segment
    '''
    pl = cl_object.get_pivotlist(outfile='data/tmp/test.png',
                                 th_up=0.01, th_down=-0.01)

    adt = datetime.datetime(2015, 8, 16, 21, 0)

    rpt = pl.fetch_by_time(adt)

    rpt.merge_pre(slist=pl.slist, n_candles=5)

    assert datetime.datetime(2015, 8, 13, 21, 0)==rpt.pre.end()

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