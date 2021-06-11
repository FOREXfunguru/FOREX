import pytest

from api.oanda.connect import Connect
from forex.candle.candlelist_utils import *
from forex.candle.candlelist import CandleList
from utils import DATA_DIR

def test_calc_SR(clO, clean_tmp):
    """
    Check 'calc_SR' function
    """
    harealst = calc_SR(clO, outfile=DATA_DIR+"/imgs/srareas/calc_sr.png")

    # check the length of HAreaList.halist
    assert len(harealst.halist) == 2

def test_calc_atr(clO, clean_tmp):
    """
    Check 'calc_atr' function
    """
    atr = calc_atr(clO)

    assert atr == 43.937

@pytest.mark.parametrize("pair,"
                         "start,"
                         "end,"
                         "n_areas",
                         [('AUD_USD', '2019-12-31T22:00:00', '2020-06-08T22:00:00', 4),
                          ('AUD_USD', '2016-12-06T22:00:00', '2020-12-20T22:00:00', 4)])
def test_calc_SR1(pair, start, end, n_areas, clean_tmp):
    """
    Check 'calc_SR' function with different CandleLists
    """

    conn = Connect(instrument=pair,
                   granularity='D' )

    res = conn.query(start= start,
                     end= end)

    clO = CandleList(res)
    harealst = calc_SR(clO, outfile=DATA_DIR+"/imgs/srareas/calc_sr.png")

    assert len(harealst.halist) == n_areas
