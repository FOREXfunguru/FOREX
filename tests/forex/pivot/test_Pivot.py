from api.oanda.connect import Connect
from forex.candle import CandleList
from params import pivots_params
from forex.pivot import PivotList

import pytest
import datetime
import pdb

@pytest.fixture
def pivot(clO_pickled):
    """Obtain a Pivot object"""

    pl = PivotList(clist=clO_pickled)
    return pl[5]

def test_pre_aft_lens(pivot):
    '''
    Check if 'pre' and 'aft' Segments have the
    correct number of candles
    '''

    assert len(pivot.pre.clist) == 39
    assert len(pivot.aft.clist) == 17

def test_pre_aft_start(pivot):
    '''
    Check if 'pre' and 'aft' Segments have the
    correct start Datetimes
    '''

    assert datetime.datetime(2011, 1, 19, 22, 0) == pivot.pre.start()
    assert datetime.datetime(2011, 2, 27, 22, 0) == pivot.aft.start()

@pytest.mark.parametrize("ix,"
                         "date_pre,"
                         "date_post",
                         [(40, datetime.datetime(2013, 8, 8, 21, 0), datetime.datetime(2013, 8, 8, 21, 0)),
                          (50, datetime.datetime(2014, 6, 30, 21, 0), datetime.datetime(2014, 6, 30, 21, 0))])
def test_merge_pre(pivotlist, ix, date_pre, date_post):
    '''
    Test function 'merge_pre'
    '''
    pivot = pivotlist.pivots[ix]
    # Check pivot.pre.start() before running 'merge_pre'
    assert date_pre == pivot.pre.start()

    pivot.merge_pre(slist=pivotlist.slist,
                    n_candles=pivots_params.n_candles,
                    diff_th=pivots_params.diff_th)

    # Check pivot.pre.start() after running 'merge_pre'
    assert date_post == pivot.pre.start()

@pytest.mark.parametrize("ix,"
                         "date_pre,"
                         "date_post",
                         [(70, datetime.datetime(2015, 10, 8, 21, 0), datetime.datetime(2015, 10, 8, 21, 0)),
                          (80, datetime.datetime(2016, 6, 21, 21, 0), datetime.datetime(2016, 11, 6, 22, 0))])
def test_merge_aft(pivotlist, ix, date_pre, date_post):
    '''
    Test function to merge 'aft' Segment
    '''
    pivot = pivotlist.pivots[ix]
    # Check pivot.aft.end() before running 'merge_aft'
    assert date_pre == pivot.aft.end()

    pivot.merge_aft(slist=pivotlist.slist,
                    n_candles=pivots_params.n_candles,
                    diff_th=pivots_params.diff_th)

    # Check pivot.aft.end() after running 'merge_aft'
    assert date_post == pivot.aft.end()

def test_calc_score_d(pivot):
    '''
    Test function named 'calc_score'
    with 'diff' parameter (def option)
    '''
    score = pivot.calc_score()

    assert score == 627.4

def test_calc_score_c(pivot):
    '''
    Test function named 'calc_score'
    with 'candle' parameter
    '''
    score = pivot.calc_score(type="candles")

    assert score == 56

@pytest.mark.parametrize("ix,"
                         "new_b",
                         [(10, datetime.datetime(2020, 11, 17, 22, 0)),
                          (20, datetime.datetime(2020, 11, 17, 22, 0)),
                          (30, datetime.datetime(2020, 11, 17, 22, 0)) ])
def test_adjust_pivottime(pivotlist, ix, new_b):
    p = pivotlist[ix]
    newt = p.adjust_pivottime(clistO=pivotlist.clist)

    assert new_b == newt