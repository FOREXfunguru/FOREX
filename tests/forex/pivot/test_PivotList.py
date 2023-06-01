import datetime
import os

from utils import DATA_DIR
from forex.pivot import PivotList


def test_get_score(pivotlist):
    """
    Test 'get_score' function
    """
    assert pivotlist.get_score() == 90358.0


def test_get_avg_score(pivotlist):
    """
    Test 'get_avg_score' function
    """
    assert pivotlist.get_avg_score() == 654.8


def test_in_area(pivotlist):
    """
    Test 'inarea_pivots' function
    """
    pl_inarea = pivotlist.inarea_pivots(price=0.75)

    # check the len of pl.plist after getting the pivots in the S/R area
    assert len(pl_inarea) == 8


def test_plot_pivots(pivotlist, clean_tmp):
    """
    Test plot_pivots
    """
    outfile = f"{DATA_DIR}/out/{pivotlist.clist.instrument}.png"
    outfile_rsi = f"{DATA_DIR}/out/{pivotlist.clist.instrument}.final_rsi.png"

    pivotlist.clist.calc_rsi()
    pivotlist.plot_pivots(outfile_prices=outfile,
                          outfile_rsi=outfile_rsi)

    assert os.path.exists(outfile) == 1
    assert os.path.exists(outfile_rsi) == 1


def test_print_pivots_dates(pivotlist):
    dtl = pivotlist.print_pivots_dates()
    assert len(dtl) == 138


def test_fetch_by_type(pivotlist):
    """Obtain a pivotlist of a certain type"""

    newpl = pivotlist.fetch_by_type(type=-1)
    assert len(newpl.pivots) == 68


def test_fetch_by_time(pivotlist):
    """Obtain a Pivot object by datetime"""

    adt = datetime.datetime(2014, 10, 2, 21, 0)
    rpt = pivotlist.fetch_by_time(adt)
    assert rpt.candle.time == datetime.datetime(2014, 10, 2, 21, 0)


def test_pivots_report(pivotlist, clean_tmp):
    """Get a PivotList report"""

    outfile = f"{DATA_DIR}/out/{pivotlist.clist.instrument}.preport.txt"
    pivotlist.pivots_report(outfile=outfile)


def test_calc_itrend(clO_pickled):
    """Calc init of trend"""
    
    subCl1 = clO_pickled.slice(start=clO_pickled.candles[0].time,
                               end=datetime.datetime(2020, 6, 10, 22, 0))
    subCl2 = clO_pickled.slice(start=clO_pickled.candles[0].time,
                               end=datetime.datetime(2020, 3, 19, 22, 0))
    subCl3 = clO_pickled.slice(start=clO_pickled.candles[0].time,
                               end=datetime.datetime(2017, 12, 8, 22, 0))

    pl1 = PivotList(clist=subCl1)
    pl2 = PivotList(clist=subCl2)
    pl3 = PivotList(clist=subCl3)

    assert pl1.calc_itrend().start() == datetime.datetime(2020, 3, 18, 21, 0)
    assert pl2.calc_itrend().start() == datetime.datetime(2019, 12, 30, 22, 0)
    assert pl3.calc_itrend().start() == datetime.datetime(2017, 9, 7, 21, 0)
