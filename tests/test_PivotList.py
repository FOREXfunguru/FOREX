from pivotlist  import PivotList
from oanda_api import OandaAPI
from candlelist import CandleList

import pytest
import glob
import os
import datetime
import pdb

@pytest.fixture
def cl_object():
    '''Returns CandleList object'''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='AUD_USD',
                     granularity='D',
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22)

    oanda.run(start='2015-06-24T22:00:00',
              end='2019-06-21T22:00:00',
              roll=True)

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list, instrument='AUD_USD', type='long')

    return cl

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('data/tmp/*')
    for f in files:
        os.remove(f)
"""
def test_get_pivotlist(cl_object):
    '''Obtain a pivotlist'''

    pl=cl_object.get_pivotlist(outfile='data/tmp/test.png',
                                th_up=0.01, th_down=-0.01)

    assert len(pl.plist)==120
    assert pl.plist[10].candle.openAsk==0.72472
    assert len(pl.plist[10].pre.clist)==10
    assert len(pl.plist[10].aft.clist) == 1

def test_fetch_by_time(cl_object):
    '''Obtain a Pivot object by datetime'''
    pl = cl_object.get_pivotlist(outfile='data/tmp/test.png',
                                 th_up=0.01, th_down=-0.01)

    adt = datetime.datetime(2016, 2, 2, 22, 0)

    rpt=pl.fetch_by_time(adt)

    assert rpt.candle.time==adt

def test_fetch_pre(cl_object):
    '''Obtain the 'pre' Segment'''

    pl = cl_object.get_pivotlist(outfile='data/tmp/test.png',
                                 th_up=0.01, th_down=-0.01)

    adt = datetime.datetime(2016, 1, 18, 22, 0)

    rpt = pl.fetch_by_time(adt)

    assert len(rpt.pre.clist) == 12

def test_merge_pre(cl_object):
    '''
    Test function to merge 'pre' Segment
    '''
    pl = cl_object.get_pivotlist(outfile='data/tmp/test.png',
                                 th_up=0.01, th_down=-0.01)

    adt = datetime.datetime(2019, 1, 3, 22, 0)

    rpt = pl.fetch_by_time(adt)

    rpt.merge_pre(slist=pl.slist, n_candles=5)

    assert datetime.datetime(2019, 1, 2, 22, 0)==rpt.pre.end()
"""
def test_merge_aft(cl_object):
    pl = cl_object.get_pivotlist(outfile='data/tmp/test.png',
                                 th_up=0.01, th_down=-0.01)

    adt = datetime.datetime(2016, 1, 18, 22, 0)

    rpt = pl.fetch_by_time(adt)

    rpt.merge_aft(slist=pl.slist, n_candles=5)

    assert datetime.datetime(2016, 3, 17, 21, 0)== rpt.aft.end()

"""
def test_mslist_attr(cl_object, clean_tmp):
    '''
    Check if mslist attribute has been
    correctly initialized
    '''

    pl = cl_object.get_pivotlist(outfile='data/tmp/test.png', th_up=0.01, th_down=-0.01)
    assert len(pl.mslist)==19
"""