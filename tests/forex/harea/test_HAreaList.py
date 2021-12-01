from forex.harea import HAreaList
from forex.harea import HArea
from forex.candle.candle import Candle
import datetime

import pytest
import glob
import os
import numpy as np
import logging
import pdb

instrument = 'AUD_USD'
granularity = 'D'

@pytest.fixture
def hlist_factory():
    log = logging.getLogger('Test for hlist_factory for '
                            'returning a list of HArea objects')
    log.debug('hlist_factory')

    hlist = []
    for p in np.arange(0.660, 0.720, 0.020):
        area = HArea(price=p,
                     pips=30,
                     instrument=instrument,
                     granularity=granularity)
        hlist.append(area)
    return hlist

def test_HAreaList_inst(hlist_factory):
    log = logging.getLogger('Instantiate a HAreaList')
    log.debug('HAreaList')

    halist = HAreaList(halist=hlist_factory)
    assert len(halist.halist) == 3

def test_onArea(hlist_factory):
    log = logging.getLogger('Test for test_onArea function')
    log.debug('test_onArea')

    halist = HAreaList(halist=hlist_factory)

    candle = {'complete': True, 
              'volume': 5937, 
              'time': datetime.datetime(2019, 3, 6, 22, 0), 
              'mid': {'o': '0.70320', 'h': '0.721', 'l': '0.719', 'c': '0.70158'}
              }

    c_candle = Candle(**candle)

    (hrsel, ix) = halist.onArea(candle=c_candle)

    assert hrsel.price == 0.70
    assert ix == 2

def test_print(hlist_factory):
    '''Test 'print' function'''

    halist = HAreaList(
        halist=hlist_factory)

    res = halist.print()
    print(res)

def test_plot(hlist_factory, clO, clean_tmp):
    '''Test 'plot' function'''

    halist = HAreaList(halist=hlist_factory)

    halist.plot(clO, outfile=os.getenv('DATADIR')+
                             "/imgs/halist/AUD_USD.halist.png")
