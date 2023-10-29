import datetime

from forex.candlelist_utils import calc_SR,  calc_atr
from params import pivots_params
from forex.pivot import PivotList


def test_calc_SR(pivotlist, tmp_path):
    """Check 'calc_SR' function"""
    harealst = calc_SR(pivotlist, outfile=f"{tmp_path}/calc_sr.png")

    assert len(harealst.halist) == 8


def test_calc_SR_H8(clOH8_pickled, tmp_path):
    """Check 'calc_SR' function for H8 dataframe"""
    # these are the recommended params for H8
    pivots_params.th_bounces = 0.02
    pivotlistH8 = PivotList(clist=clOH8_pickled.
                            slice(start=clOH8_pickled.candles[0].time,
                                  end=datetime.datetime(2021, 10, 29, 5, 0)))
    harealst = calc_SR(pivotlistH8, outfile=f"{tmp_path}/calc_sr_h8.png")
    assert len(harealst.halist) == 3


def test_calc_atr(clO):
    """Check 'calc_atr' function"""
    atr = calc_atr(clO)

    assert atr == 374.1
