from oanda.connect import Connect
from candle.candlelist import CandleList
from config import CONFIG

import pytest
import glob
import os
import datetime

def test_get_pivotlist(clO):
    """Obtain a pivotlist"""

    pl = clO.get_pivotlist(th_bounces=CONFIG.getfloat('pivots', 'th_bounces'))
    assert len(pl.plist) == 11
    assert pl.plist[10].candle['openAsk'] == 0.68495
    assert len(pl.plist[7].pre.clist) == 23
    assert len(pl.plist[9].aft.clist) == 17

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
