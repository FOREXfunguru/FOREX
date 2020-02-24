from pivotlist  import PivotList
from oanda_api import OandaAPI
from candlelist import CandleList

import pytest
import glob
import os
import datetime
import pdb

@pytest.fixture
def cl_object():
    '''Returns CandleList object'''

    oanda = OandaAPI(instrument='AUD_USD',
                     granularity='D',
                     settingf='/data/settings.ini')

    oanda.run(start='2015-06-24T22:00:00',
              end='2019-06-21T22:00:00')

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list,
                    instrument='AUD_USD',
                    type='long',
                    settingf='/data/settings.ini')

    return cl

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('data/tmp/*')
    for f in files:
        os.remove(f)

def test_get_pivotlist(cl_object):
    '''Obtain a pivotlist'''

    pl=cl_object.get_pivotlist()

    assert len(pl.plist) == 120
    assert pl.plist[10].candle.openAsk == 0.72472
    assert len(pl.plist[7].pre.clist) == 7
    assert len(pl.plist[10].aft.clist) == 2


def test_fetch_by_type(cl_object):
    '''Obtain a pivotlist of a certain type'''

    pl = cl_object.get_pivotlist()

    newpl = pl.fetch_by_type(type=-1)

    assert len(newpl.plist) == 60

def test_fetch_by_time(cl_object):
    '''Obtain a Pivot object by datetime'''
    pl = cl_object.get_pivotlist(outfile='data/tmp/test.png',
                                 th_up=0.01, th_down=-0.01)

    adt = datetime.datetime(2016, 2, 2, 22, 0)

    rpt=pl.fetch_by_time(adt)

    assert rpt.candle.time==adt