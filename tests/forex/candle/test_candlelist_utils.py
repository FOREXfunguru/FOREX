import pytest

from forex.candlelist_utils import *
from utils import DATA_DIR

def test_calc_SR(pivotlist, clean_tmp):
    """Check 'calc_SR' function"""
    harealst = calc_SR(pivotlist, outfile=DATA_DIR+"/out/calc_sr.png")

    assert len(harealst.halist) == 8

def test_calc_atr(clO, clean_tmp):
    """Check 'calc_atr' function"""
    atr = calc_atr(clO)

    assert atr == 374.1

