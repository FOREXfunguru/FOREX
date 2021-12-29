'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
import os
import logging
import pdb
import datetime

from utils import DATA_DIR
from forex.candle import CandleList

def test_candlelist_inst(clO):
    log = logging.getLogger('Test CandleList instantiation')
    log.debug('CandleList instantation')
    assert clO.type == 'short'
    assert clO[0].colour == 'red'
    assert len(clO) == 2

def test_pickle_dump(clO):
    log = logging.getLogger('Test for pickle_dump')
    log.debug('pickle_dump')

    clO.pickle_dump(DATA_DIR+"/out/clist.pckl")

    assert os.path.exists(DATA_DIR+"/out/clist.pckl") == 1

def test_pickle_load(clean_tmp):
    log = logging.getLogger('Test for pickle_load')
    log.debug('pickle_load')

    loadedCL = CandleList.pickle_load(DATA_DIR+"/out/clist.pckl")
    assert loadedCL.instrument == 'AUD_USD'
    assert len(loadedCL) == 2

def test_calc_rsi(clO_pickled):
    log = logging.getLogger('Test for calc_rsi function')
    log.debug('calc_rsi')

    clO_pickled.calc_rsi()

    assert clO_pickled[15].rsi == 61.54
    assert clO_pickled[50].rsi == 48.59

def test_rsibounces(clO_pickled):
    log = logging.getLogger('Test for rsi_bounces function')
    log.debug('rsi_bounces')

    clO_pickled.calc_rsi()
    dict1 = clO_pickled.calc_rsi_bounces()

    dict2 = {'number': 31,
             'lengths': [1, 1, 3, 4, 5, 7, 1, 1, 
             4, 5, 4, 3, 1, 1, 4, 5, 1, 2, 1, 1, 
             1, 1, 12, 7, 14, 3, 8, 2, 3, 1, 3]}

    assert dict1 == dict2

def test_get_length_pips(clO_pickled):
    '''
    This test check the functions for getting the length of
    the CandleList in number of pips and candles
    '''
    log = logging.getLogger('Test for different length functions')
    log.debug('get_length')

    assert clO_pickled.get_length_pips() == 2493

def test_fetch_by_time(clO_pickled):

    adatetime = datetime.datetime(2019, 5, 7, 22, 0)
    c = clO_pickled.fetch_by_time(adatetime)

    assert c.o == 0.70118
    assert c.h == 0.70270

def test_slice_with_start(clO_pickled):

    adatetime = datetime.datetime(2019, 5, 7, 21, 0)

    new_cl = clO_pickled.slice(start = adatetime)

    assert len(new_cl) == 401

def test_slice_with_start_end(clO_pickled):

    startdatetime = datetime.datetime(2019, 5, 7, 21, 0)
    endatetime = datetime.datetime(2019, 7, 1, 21, 0)

    new_cl = clO_pickled.slice(start=startdatetime,
                               end=endatetime)

    assert len(new_cl) == 40

def test_last_time(clO_pickled):
    log = logging.getLogger('Test for last_time function')
    log.debug('last_time')

    lt = clO_pickled.get_lasttime(price=0.78608)
    assert lt.isoformat() == '2018-02-19T22:00:00'

def test_get_highest(clO_pickled):
    log = logging.getLogger('Test get_highest')
    log.debug('get_highest')

    clO_pickled.get_highest()

    assert clO_pickled.get_highest() == 1.10307

def test_get_lowest(clO_pickled):
    log = logging.getLogger('Test get_lowest')
    log.debug('get_lowest')

    clO_pickled.get_lowest()

    assert clO_pickled.get_lowest() == 0.57444