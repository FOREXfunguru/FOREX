import pytest
import datetime

from forex.candlelist_utils import *
from utils import DATA_DIR
from params import tradebot_params, pivots_params
from forex.pivot import PivotList

def test_calc_SR(pivotlist, clean_tmp):
    """Check 'calc_SR' function"""
    harealst = calc_SR(pivotlist, outfile=DATA_DIR+"/out/calc_sr.png")

    assert len(harealst.halist) == 8

def test_calc_SR_H8(clOH8_pickled, clean_tmp):
    """Check 'calc_SR' function for H8 dataframe"""
    # these are the recommended params for H8
    pivots_params.th_bounces=0.02
    pivotlistH8 = PivotList(clist=clOH8_pickled.slice(start=clOH8_pickled.candles[0].time, end=datetime(2021, 10, 29, 5, 0)))
    harealst = calc_SR(pivotlistH8, outfile=DATA_DIR+"/out/calc_sr_h8.png")
    assert len(harealst.halist) == 2

def test_calc_atr(clO, clean_tmp):
    """Check 'calc_atr' function"""
    atr = calc_atr(clO)

    assert atr == 374.1

