from harea.harealist import HAreaList
from harea.harea import HArea
from candle.candle import BidAskCandle

import pytest
import glob
import os
import numpy as np

instrument = 'AUD_USD'
granularity = 'D'

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('../data/IMGS/pivots/*')
    for f in files:
        os.remove(f)

@pytest.fixture
def hlist_factory():
    '''Returns a list of HArea objects'''

    hlist = []
    for p in np.arange(0.67116, 0.82877, 0.042):
        area = HArea(price=p,
                     pips=30,
                     instrument=instrument,
                     granularity=granularity,
                     settingf='../../data/settings.ini')
        hlist.append(area)

    return hlist

def test_HAreaList_inst(hlist_factory):
    '''Test instantiation of a HAreaList object'''

    halist = HAreaList(
        halist=hlist_factory,
        settingf="data/settings.ini"
    )
    assert len(halist.halist) == 4

def test_onArea(hlist_factory):
    '''Test onArea function'''

    halist = HAreaList(
        halist=hlist_factory,
        settingf="../../data/settings.ini"
    )
    candle = BidAskCandle(openAsk=0.71195,
                          openBid=0.71195,
                          granularity='D',
                          instrument='AUD_USD',
                          closeAsk=0.71619,
                          closeBid=0.71619,
                          highAsk=0.71767,
                          highBid=0.71767,
                          lowAsk=0.70983,
                          lowBid=0.70983,
                          complete=True,
                          volume=12619,
                          representation='bidask',
                          time='2015-08-26 22:00:00')

    hrsel = halist.onArea(candle=candle)
    #check if HArea.price is between candle.lowAsk and candle.HighAsk
    assert hrsel.price == 0.7132

def test_print(hlist_factory):
    '''Test 'print' function'''

    halist = HAreaList(
        halist=hlist_factory,
        settingf="../../data/settings.ini"
    )

    halist.print()

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('../data/IMGS/pivots/*.png')
    for f in files:
        os.remove(f)
