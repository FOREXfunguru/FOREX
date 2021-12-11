from forex.params import pivots_params

import pytest
import datetime
import pdb
import os

@pytest.fixture
def pivotlist(clO_pickled):
    """Obtain a PivotList object"""

    pdb.set_trace()
    pl, modes = clO_pickled.get_pivotlist(th_bounces=pivots_params.th_bounces)

    PivotList(clist=clO_pickled)
    return pl

def test_get_score(clO):
    """
    Test 'get_score' function
    """
    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))
    assert pl.get_score() == 3932.8

def test_get_avg_score(clO):
    """
    Test 'get_avg_score' function
    """
    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))
    assert pl.get_avg_score() == 357.5

def test_in_area(clO, clean_tmp):
    """
    Test 'inarea_pivots' function
    """
    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))
    # check the len of pl.plist before getting the pivots in the S/R area
    assert len(pl.plist) == 11
    pl_inarea = pl.inarea_pivots(SR=0.67117)

    # check the len of pl.plist after getting the pivots in the S/R area
    assert len(pl_inarea.plist) == 3

def test_get_pl_bytime(clO, clean_tmp):
    """
    Test 'get_pl_bytime"
    """
    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))
    dt = datetime.datetime(2019, 7, 1, 21, 0)
    newpl = pl.get_pl_bytime(adatetime=dt)
    assert len(newpl.plist) == 8

def test_plot_pivots(clO, clean_tmp):
    """
    Test plot_pivots
    """

    clO.calc_rsi()
    outfile = CONFIG.get('images', 'outdir') + "/pivots/{0}.png".format(clO.data['instrument'].
                                                                                    replace(' ', '_'))
    outfile_rsi = CONFIG.get('images', 'outdir') + "/pivots/{0}.final_rsi.png".format(clO.data['instrument'].
                                                                                      replace(' ', '_'))
    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))

    pl.plot_pivots(outfile_prices=outfile,
                   outfile_rsi=outfile_rsi)

    assert os.path.exists(outfile) == 1
    assert os.path.exists(outfile_rsi) == 1

def test_print_pivots_dates(clO):
    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))
    dtl = pl.print_pivots_dates()
    assert len(dtl) == 11

def test_fetch_by_type(clO):
    """Obtain a pivotlist of a certain type"""

    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))
    newpl = pl.fetch_by_type(type=-1)
    assert len(newpl.plist) == 6

def test_fetch_by_time(clO):
    """Obtain a Pivot object by datetime"""

    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))

    adt = datetime.datetime(2019, 4, 16, 21, 0)
    rpt = pl.fetch_by_time(adt)
    assert rpt.candle['time'] == datetime.datetime(2019, 4, 16, 21, 0)

def test_pivots_report(clO, clean_tmp):
    """Get a PivotList report"""

    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))
    routfile = CONFIG.get('images', 'outdir') + "/pivots_report/{0}.preport.txt".format(clO.data['instrument'].
                                                                                        replace(' ', '_'))
    pl.pivots_report(outfile=routfile)