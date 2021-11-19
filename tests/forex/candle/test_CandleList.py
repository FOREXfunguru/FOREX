'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
import pytest
import datetime
import glob
import os
import logging
import pdb

from forex.candle.candlelist import CandleList
from api.oanda.connect import Connect
from forex.harea import HArea
from utils import DATA_DIR

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob(DATA_DIR+"/imgs/**/*.png",recursive=True)
    for f in files:
        os.remove(f)

@pytest.mark.parametrize("ix,"
                        "rsi",
                        [(4, 48.42),
                         (51, 25.63),
                         (130, 53.63),
                         (136, 62.97),
                         (212, 73.64)])
def test_calc_rsi(ix, rsi, clO):
    log = logging.getLogger('Test for calc_rsi function')
    log.debug('calc_rsi')

    clO.calc_rsi()
    assert clO.data['candles'][ix]['rsi'] == rsi

def test_rsibounces(clO):
    log = logging.getLogger('Test for rsi_bounces function')
    log.debug('rsi_bounces')

    clO.calc_rsi()
    dict1 = clO.calc_rsi_bounces()

    dict2 = {'number': 1,
             'lengths': [3]}

    assert dict1 == dict2

def test_get_length_functions(clO):
    '''
    This test check the functions for getting the length of
    the CandleList in number of pips and candles
    '''
    log = logging.getLogger('Test for different length functions')
    log.debug('get_length')

    assert clO.get_length_candles() == 230
    assert clO.get_length_pips() == 191

def test_fetch_by_time(clO):

    adatetime = datetime.datetime(2019, 5, 7, 22, 0)
    c = clO.fetch_by_time(adatetime)

    assert float(c['mid']['o']) == 0.70118
    assert float(c['mid']['h']) == 0.70270

def test_slice_with_start(clO):

    adatetime = datetime.datetime(2019, 5, 7, 22, 0)

    new_cl = clO.slice(start = adatetime)

    assert len(new_cl.data['candles']) == 185

def test_slice_with_start_end(clO):

    startdatetime = datetime.datetime(2019, 5, 7, 22, 0)
    endatetime = datetime.datetime(2019, 7, 1, 22, 0)

    new_cl = clO.slice(start=startdatetime,
                       end=endatetime)

    assert len(new_cl.data['candles']) == 39

def test_get_lasttime():
    log = logging.getLogger('Test for get_lasttime')
    log.debug('get_lasttime')

    conn= Connect(instrument='AUD_CHF',
                  granularity='H12')

    resist = HArea(price=1.00721,
                   pips=45,
                   instrument='AUD_CHF',
                   granularity='H12')

    res = conn.query(start='2004-11-07T10:00:00',
                     end='2010-04-30T09:00:00')

    cl = CandleList(res, type='short')

    lasttime = cl.get_lasttime(resist)
    assert lasttime == datetime.datetime(2007, 11, 9, 10, 0)

def test_get_highest(clO):
    clO.get_highest()

    assert clO.get_highest() == 0.71789

def test_get_lowest(clO):
    clO.get_lowest()

    assert clO.get_lowest() == 0.67038

@pytest.mark.parametrize("pair,"
                         "start,"
                         "end,"
                         "t_type,"
                         'itrend',
                         [('AUD_CAD', datetime.datetime(2009, 7, 8, 22, 0),
                           datetime.datetime(2012, 5, 28, 22, 0), 'long', datetime.datetime(2012, 2, 7, 22, 0)),
                          ('AUD_CAD', datetime.datetime(2009, 7, 8, 22, 0),
                           datetime.datetime(2012, 9, 6, 22, 0), 'long', datetime.datetime(2012, 8, 4, 21, 0)),
                          ('AUD_CAD', datetime.datetime(2009, 7, 8, 22, 0),
                           datetime.datetime(2012, 10, 8, 22, 0), 'long', datetime.datetime(2012, 8, 4, 21, 0)),
                          ('AUD_CAD', datetime.datetime(2012, 6, 5, 22, 0),
                           datetime.datetime(2012, 9, 5, 22, 0), 'long', datetime.datetime(2012, 8, 4, 21, 0)),
                          ('AUD_USD', datetime.datetime(2014, 1, 1, 22, 0),
                           datetime.datetime(2015, 9, 10, 22, 0), 'long', datetime.datetime(2015, 6, 17, 21, 0)),
                          ('AUD_USD', datetime.datetime(2019, 7, 12, 22, 0),
                           datetime.datetime(2019, 8, 6, 22, 0), 'long', datetime.datetime(2019, 7, 14, 21, 0)),
                          ('AUD_USD', datetime.datetime(2017, 5, 7, 22, 0),
                           datetime.datetime(2017, 12, 12, 22, 0), 'long', datetime.datetime(2017, 9, 7, 21, 0)),
                          ('AUD_USD', datetime.datetime(2014, 1, 2, 22, 0),
                           datetime.datetime(2015, 10, 1, 22, 0), 'long', datetime.datetime(2015, 9, 15, 21, 0)),
                          ('AUD_USD', datetime.datetime(2012, 2, 29, 22, 0),
                           datetime.datetime(2013, 8, 5, 22, 0), 'long', datetime.datetime(2013, 7, 22, 21, 0)),
                          ('AUD_USD', datetime.datetime(2012, 2, 27, 22, 0),
                           datetime.datetime(2012, 9, 7, 22, 0), 'long', datetime.datetime(2012, 8, 8, 21, 0)),
                          ('AUD_USD', datetime.datetime(2015, 9, 7, 22, 0),
                           datetime.datetime(2016, 4, 25, 22, 0), 'short', datetime.datetime(2016, 1, 17, 22, 0))])
def test_calc_itrend(pair, start, end, t_type, itrend, clean_tmp):
    log = logging.getLogger('Test for calc_itrend')
    log.debug('calc_itrend')

    conn = Connect(instrument=pair,
                   granularity='D')

    res = conn.query(start=start.isoformat(),
                     end=end.isoformat())

    cl = CandleList(res)

    assert itrend == cl.calc_itrend().start()