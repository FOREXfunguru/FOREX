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

from oanda.connect import Connect
from candle.candlelist import CandleList
from harea import HArea

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    pdb.set_trace()
    files = glob.glob(os.getenv('DATADIR')+"/imgs/**/*.png",recursive=True)
    for f in files:
        os.remove(f)

@pytest.mark.parametrize("ix,"
                        "rsi",
                        [(4, 48.2),
                         (51, 25.94),
                         (130, 53.37),
                         (136, 63.26),
                         (212, 73.1)])
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
    assert clO.get_length_pips() == 190

def test_fit_reg_line(clO, clean_tmp):
    log = logging.getLogger('Test for fit_reg_line function')
    log.debug('get_length')
    (fitted_model, regression_model_mse) = clO.fit_reg_line(outdir=os.getenv('DATADIR')+"/imgs")

    assert regression_model_mse == 1.8643961557713323e-05

def test_fetch_by_time(clO):

    adatetime = datetime.datetime(2019, 5, 7, 22, 0)

    c = clO.fetch_by_time(adatetime)

    assert c['openAsk'] == 0.70137
    assert c['highAsk'] == 0.70277

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
    oanda = Connect(instrument='AUD_CHF',
                    granularity='H12')

    resist = HArea(price=1.00721,
                   pips=45,
                   instrument='AUD_CHF',
                   granularity='H12')

    oanda.run(start='2004-11-07T10:00:00',
              end='2010-04-30T09:00:00')

    candle_list = oanda.fetch_candleset()
    cl = CandleList(candle_list,
                    instrument='AUD_CHF',
                    id='test_AUD_CHF_clist',
                    granularity='H12',
                    type='short',
                    settingf='../../data/settings.ini')

    lasttime = cl.get_lasttime(resist)
    assert lasttime == datetime.datetime(2007, 11, 9, 10, 0)
"""
def test_get_highest(clO):
    clO.get_highest()

    assert clO.get_highest() == 0.718

def test_get_lowest(clO):
    clO.get_lowest()

    assert clO.get_lowest() == 0.67047


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
def test_calc_itrend(pair, start, end, t_type, itrend, settings_obj, clean_tmp):

    settings_obj.set('it_trend', 'th_bounces', '0.02')
    settings_obj.set('it_trend', 'n_candles', '12')

    oanda = OandaAPI(instrument=pair,
                     granularity='D',
                     settings=settings_obj)

    oanda.run(start=start.isoformat(),
              end=end.isoformat())

    candle_list = oanda.fetch_candleset()
    cl = CandleList(candle_list,
                    instrument=pair,
                    id='test_clist',
                    granularity='D',
                    settings=settings_obj)

    assert itrend == cl.calc_itrend(t_type=t_type)

def test_check_if_divergence():

    conn = Connect(instrument='EUR_AUD',
                    granularity='D')

    conn.query(start='2016-05-23T23:00:00',
               end='2016-07-19T23:00:00')

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list,
                    instrument='CAD_JPY',
                    granularity='D')

    cl.calc_rsi()

    (model, outfile) = cl.fit_reg_line()

    direction = None
    if model.coef_[0, 0] > 0:
        direction = 'up'
    else:
        direction = 'down'

    assert cl.check_if_divergence(direction=direction) == True

def get_dictionary(k, v):
    d = dict([x, ord(x)] for x in  string.printable)
    d[k] = v
    return d

def test_calc_binary_seq(oanda_object):
    
    candle_list=oanda_object.fetch_candleset()

    cl=CandleList(candle_list, type='short')

    cl.calc_binary_seq(merge=False)
    dict1=cl.seq
    dict2={'open': '01', 'colour': '011', 'high': '01', 'close': '11', 'low': '11'}

    shared_items = set(dict1.items()) & set(dict2.items())

    assert len(shared_items) == 5

def test_calc_binary_seq_withmerge(oanda_object):
    '''
    Test the calc_binary_seq function with the merge=True option
    '''

    candle_list=oanda_object.fetch_candleset()

    cl=CandleList(candle_list, type='short')

    cl.calc_binary_seq(merge=True)
    dict1=cl.seq
    dict2={'close': '11', 'colour': '011', 'merge': '01110111011', 'open': '01', 'high': '01', 'low': '11'}

    shared_items = set(dict1.items()) & set(dict2.items())

    assert len(shared_items) == 6

def test_number_of_0s(oanda_object):
  
    candle_list=oanda_object.fetch_candleset()
    
    cl=CandleList(candle_list, type='short')

    cl.calc_binary_seq()

    cl.calc_number_of_0s(norm=True)

    dict1=cl.number_of_0s
    dict2={'open': 0.5, 'close': 0.0, 'colour': 0.3333333333333333, 'low': 0.0, 'high': 0.5, 'merge':0.2727272727272727}

    shared_items = set(dict1.items()) & set(dict2.items())

    assert len(shared_items) == 6

def test_calc_number_of_doubles0s(oanda_object):
    
    candle_list=oanda_object.fetch_candleset()

    cl=CandleList(candle_list, type='short')

    cl.calc_binary_seq()

    cl.calc_number_of_doubles0s(norm=True)

    assert cl.highlow_double0s==0.0
    assert cl.openclose_double0s==0.0

def test_longest_stretch(oanda_object):

    candle_list=oanda_object.fetch_candleset()

    cl=CandleList(candle_list, type='short')

    cl.calc_binary_seq()

    cl.calc_longest_stretch()

    dict1=cl.longest_stretch
    dict2={'close': 0, 'high': 0, 'open': 0, 'low': 0, 'colour': 0}

    shared_items = set(dict1.items()) & set(dict2.items())

    assert len(shared_items) == 5

def test_get_entropy(oanda_object):
    
    candle_list=oanda_object.fetch_candleset()

    cl=CandleList(candle_list, type='short')

    cl.calc_binary_seq()

    cl.get_entropy()

    dict1=cl.entropy
    dict2={'open': 0.34657359027997264, 'colour': 0.21217138943160427, 'high': 0.34657359027997264, 'close': 0.0, 'low': 0.0}

    shared_items = set(dict1.items()) & set(dict2.items())

    assert len(shared_items) == 5
"""
