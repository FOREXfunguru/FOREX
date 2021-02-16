from oanda.connect import Connect
from candle.candlelist import CandleList
from config import CONFIG

import pytest
import datetime
import pdb

def test_pre_aft_lens(clO, clean_tmp):
    '''
    Check if 'pre' and 'aft' Segments have the
    correct number of candles
    '''

    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))

    pivot = pl.plist[3]

    assert len(pivot.pre.clist) == 23
    assert len(pivot.aft.clist) == 32

def test_pre_aft_start(clO, clean_tmp):
    '''
    Check if 'pre' and 'aft' Segments have the
    correct start Datetimes
    '''

    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))

    pivot = pl.plist[3]

    assert datetime.datetime(2019, 6, 16, 21, 0) == pivot.pre.start()
    assert datetime.datetime(2019, 7, 17, 21, 0) == pivot.aft.start()

@pytest.mark.parametrize("ix,"
                         "pair,"
                         "timeframe,"
                         "id,"
                         "start,"
                         "end,"
                         "date_pre,"
                         "date_post",
                         [
                          (-1, 'AUD_USD', 'H1', 'AUD_USD 13MAR2020H12', '2020-03-01T22:00:00',
                           '2020-04-01T22:00:00', datetime.datetime(2019, 5, 22, 21, 0),
                           datetime.datetime(2019, 5, 22, 21, 0)),
                          (-1, 'EUR_JPY', 'D', 'EUR_JPY 27OCT2009D', '2004-02-03T21:00:00',
                           '2004-05-16T21:00:00', datetime.datetime(2004, 4, 4, 21, 0),
                           datetime.datetime(2004, 4, 4, 21, 0))])
def test_merge_pre(ix, pair, timeframe, id, start, end, date_pre, date_post, clean_tmp):
    '''
    Test function 'merge_pre' to merge the 'pre' Segment
    '''
    pdb.set_trace()
    conn = Connect(instrument=pair,
                    granularity=timeframe)

    res = conn.query(start=start,
                     end=end)
    cl = CandleList(res)
    pl = cl.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))

    pivot = pl.plist[ix]
    # Check pivot.pre.start() before running 'merge_pre'
   # assert date_post == pivot.pre.start()

    # run 'merge_pre' function
    pivot.merge_pre(slist=pl.slist,
                    n_candles=CONFIG.getint('pivots', 'n_candles'),
                    diff_th=CONFIG.getint('pivots', 'diff_th'))

    # Check pivot.pre.start() after running 'merge_pre'
    assert date_pre == pivot.pre.start()

def test_merge_aft(clO, clean_tmp):
    '''
    Test function to merge 'aft' Segment
    '''
    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))

    pivot = pl.plist[3]

    # Check pivot.aft.end() before running 'merge_aft'
    assert datetime.datetime(2019, 8, 29, 21, 0) == pivot.aft.end()

    # run 'merge_aft' function
    pivot.merge_aft(slist=pl.slist,
                    n_candles=CONFIG.getint('pivots', 'n_candles'),
                    diff_th=CONFIG.getint('pivots', 'diff_th'))

    # Check pivot.aft.end() after running 'merge_aft'

    assert datetime.datetime(2019, 9, 29, 21, 0) == pivot.aft.end()

def test_calc_score_d(clO, clean_tmp):
    '''
    Test function named 'calc_score'
    with 'diff' parameter (def option)
    '''
    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))

    pivot = pl.plist[3]
    score = pivot.calc_score()

    assert score == 489.8

def test_calc_score_c(clO, clean_tmp):
    '''
    Test function named 'calc_score'
    with 'candle' parameter
    '''
    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))

    pivot = pl.plist[3]
    score = pivot.calc_score(type="candles")

    assert score == 55

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
    conn = Connect(instrument=pair,
                   granularity=timeframe)

    res = conn.query(start=start,
                     end=end)


    cl = CandleList(res)
    pl = cl.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))
    p = pl.plist[ix]
    newt = p.adjust_pivottime(clistO=cl)

    assert new_b == newt