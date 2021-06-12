from forex.harea import HAreaList
from forex.harea import HArea
from forex.candle.candle import Candle

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
    assert len(halist.halist) == 4

def test_onArea(hlist_factory):
    log = logging.getLogger('Test for test_onArea function')
    log.debug('test_onArea')

    halist = HAreaList(halist=hlist_factory)

    candle = {'openAsk' : 0.69,
              'openBid' : 0.69,
              'granularity' : 'D',
              'instrument' : 'AUD_USD',
              'closeAsk' : 0.67,
              'closeBid' : 0.67,
              'highAsk' : 0.70,
              'highBid' : 0.70,
              'lowAsk' : 0.66,
              'lowBid' : 0.66,
              'complete' : True,
              'volume' : 12619,
              'time' : '2015-08-26 22:00:00'}
    c_candle = Candle(dict_data=candle)

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
