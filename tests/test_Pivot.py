from oanda_api import OandaAPI
from candlelist import CandleList

import pytest
import glob
import os
import datetime
import pdb

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('data/IMGS/pivots/*')
    for f in files:
        os.remove(f)


@pytest.fixture
def cl_object(clean_tmp):
    '''Returns CandleList object'''

    oanda = OandaAPI(instrument='AUD_USD',
                     granularity='D',
                     settingf='data/settings.ini')

    oanda.run(start='2015-06-24T22:00:00',
              end='2019-06-21T22:00:00')

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list,
                    instrument='AUD_USD',
                    id='AUD_USD_testclist',
                    type='long',
                    settingf='data/settings.ini')
    return cl

def test_pre_aft_lens(cl_object, clean_tmp):
    '''
    Check if 'pre' and 'aft' Segments have the
    correct number of candles
    '''

    pl = cl_object.get_pivotlist()

    pivot = pl.plist[3]

    assert len(pivot.pre.clist) == 21
    assert len(pivot.aft.clist) == 18

def test_pre_aft_start(cl_object, clean_tmp):
    '''
    Check if 'pre' and 'aft' Segments have the
    correct start Datetimes
    '''

    pl = cl_object.get_pivotlist()

    pivot = pl.plist[3]

    assert datetime.datetime(2015, 10, 11, 21, 0) == pivot.pre.start()
    assert datetime.datetime(2015, 11, 9, 22, 0) == pivot.aft.start()

@pytest.mark.parametrize("ix,"
                         "pair,"
                         "timeframe,"
                         "id,"
                         "start,"
                         "end,"
                         "date_pre,"
                         "date_post",
                         # This date wil skip the merge, as %_diff is greater than threshold
                         [(-1, 'NZD_USD', 'H12', 'NZD_USD 01JUL2019H12', '2019-03-26T21:00:00',
                           '2019-07-01T09:00:00', datetime.datetime(2019, 5, 22, 21, 0),
                           datetime.datetime(2019, 5, 22, 21, 0))])
def test_merge_pre(ix, pair, timeframe, id, start, end, date_pre, date_post, clean_tmp):
    '''
    Test function 'merge_pre' to merge the 'pre' Segment
    '''

    oanda = OandaAPI(instrument=pair,
                     granularity=timeframe,
                     settingf='data/settings.ini')

    oanda.run(start=start,
              end=end)

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list,
                    instrument=pair,
                    id=id,
                    settingf='data/settings.ini')

    pl = cl.get_pivotlist()

    pivot = pl.plist[ix]
    # Check pivot.pre.start() before running 'merge_pre'
    assert date_post == pivot.pre.start()

    # run 'merge_pre' function
    pivot.merge_pre(slist=pl.slist)

    # Check pivot.pre.start() after running 'merge_pre'
    assert datetime.datetime(2019, 5, 22, 21, 0) == pivot.pre.start()

def test_merge_aft(cl_object, clean_tmp):
    '''
    Test function to merge 'aft' Segment
    '''
    pl = cl_object.get_pivotlist()

    pivot = pl.plist[3]

    # Check pivot.aft.end() before running 'merge_aft'
    assert datetime.datetime(2015, 12, 2, 22, 0) == pivot.aft.end()

    # run 'merge_aft' function
    pivot.merge_aft(slist=pl.slist)

    # Check pivot.aft.end() after running 'merge_aft'

    assert datetime.datetime(2015, 12, 2, 22, 0) == pivot.aft.end()

def test_calc_score(cl_object, clean_tmp):
    '''
    Test function named 'calc_score'
    '''
    pl = cl_object.get_pivotlist()

    pivot = pl.plist[3]
    score = pivot.calc_score()

    assert score == 39

@pytest.mark.parametrize("ix,"
                         "pair,"
                         "timeframe,"
                         "id,"
                         "start,"
                         "end,"
                         "new_b",
                         [(-1, 'GBP_USD', 'D', 'GBP_USD 18APR2018D', '2018-03-01T22:00:00',
                           '2018-04-18T22:00:00', datetime.datetime(2018, 4, 15, 21, 0)),
                          (-1, 'EUR_JPY', 'D', 'EUR_JPY 15JUL2009D', '2009-05-01T22:00:00',
                           '2009-07-14T22:00:00', datetime.datetime(2009, 7, 11, 21, 0)),
                          (-1, 'EUR_AUD', 'D', 'EUR_AUD 24MAY2019D', '2009-02-23T22:00:00',
                           '2009-05-23T22:00:00',datetime.datetime(2009, 5, 18, 21, 0)) ])
def test_adjust_pivottime(ix, pair, timeframe, id, start, end, new_b, clean_tmp):
    oanda = OandaAPI(instrument=pair,
                     granularity=timeframe,
                     settingf='data/settings.ini')

    oanda.run(start=start,
              end=end)

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list,
                    instrument=pair,
                    id=id,
                    settingf='data/settings.ini')

    pl = cl.get_pivotlist()

    p = pl.plist[ix]
    newt = p.adjust_pivottime()

    assert new_b == newt