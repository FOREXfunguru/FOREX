import pytest

from apis.oanda_api import OandaAPI
from candle.candlelist import CandleList
from harea.harea import HArea

import datetime
import glob
import os

@pytest.fixture
def clO():
    """Returns a CandleList object"""

    oanda = OandaAPI(instrument='AUD_USD',
                     granularity='D',
                     settingf='../../data/settings.ini')

    oanda.run(start='2019-03-06T23:00:00',
              end='2020-01-03T23:00:00')

    candle_list = oanda.fetch_candleset()
    cl = CandleList(candle_list,
                    instrument='AUD_USD',
                    id='test_AUD_USD_clist',
                    granularity='D',
                    settingf='../../data/settings.ini')
    return cl

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('../../data/IMGS/pivots/*.png')
    for f in files:
        os.remove(f)

def test_CandleList(clO):
    """
    Test the creation of a CandleList object
    """

    one_c = clO.next()
    assert one_c.highBid == 0.70507
    assert one_c.openBid == 0.70308
    assert one_c.lowBid == 0.70047
    assert one_c.representation == 'bidask'
    assert one_c.lowAsk == 0.7006
    assert one_c.complete is True
    assert one_c.openAsk == 0.70331
    assert one_c.highAsk == 0.70521
    assert one_c.highBid == 0.70507
    assert one_c.volume == 5937
    assert one_c.closeBid == 0.70149

def test_calc_rsi(clO):

    clO.calc_rsi()

    assert clO.clist[4].rsi == 48.197810051105556

def test_rsibounces(clO):

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

    assert clO.get_length_candles() == 215
    assert clO.get_length_pips() == 61

def test_fit_reg_line(clO):

    (fitted_model, regression_model_mse) = clO.fit_reg_line()

    assert regression_model_mse == 1.2922934217942994e-05

def test_fetch_by_time(clO):

    adatetime = datetime.datetime(2019, 5, 7, 22, 0)

    c = clO.fetch_by_time(adatetime)

    assert c.openAsk == 0.70137
    assert c.highAsk == 0.70277

def test_slice_with_start(clO):

    adatetime = datetime.datetime(2019, 5, 7, 22, 0)

    new_cl = clO.slice(start=adatetime)

    assert len(new_cl.clist) == 170

def test_slice_with_start_end(clO):

    startdatetime = datetime.datetime(2019, 5, 7, 22, 0)
    endatetime = datetime.datetime(2019, 7, 1, 22, 0)

    clO.slice(start=startdatetime,
              end=endatetime)

    assert len(clO.clist) == 215

def test_get_lasttime():
    oanda = OandaAPI(instrument='AUD_CHF',
                     granularity='H12',
                     settingf='../../data/settings.ini')

    resist = HArea(price=1.00721,
                   pips=45,
                   instrument='AUD_CHF',
                   granularity='H12',
                   settingf='../../data/settings.ini')

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

def test_get_highest(clO):
    clO.get_highest()

    assert clO.get_highest() == 0.718

def test_get_lowest(clO):
    clO.get_lowest()

    assert clO.get_lowest() == 0.67047


@pytest.mark.parametrize("start,"
                         "end",
                         [(datetime.datetime(2019, 7, 12, 22, 0), datetime.datetime(2019, 8, 6, 22, 0))])
def test_calc_itrend(start, end, clean_tmp):
    oanda = OandaAPI(instrument='AUD_USD',
                     granularity='D',
                     settingf='../../data/settings.ini')

    oanda.run(start=start.isoformat(),
              end=end.isoformat())

    candle_list = oanda.fetch_candleset()
    cl = CandleList(candle_list,
                    instrument='AUD_USD',
                    id='test_AUD_USD_clist',
                    granularity='D',
                    settingf='../../data/settings.ini')
    cl.calc_itrend()

"""
def test_check_if_divergence():

    oanda = OandaAPI(instrument='EUR_AUD',
                     granularity='D',
                     settingf='data/settings.ini')

    oanda.run(start='2016-05-23T23:00:00',
              end='2016-07-19T23:00:00')

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list,
                    instrument='CAD_JPY',
                    granularity='D',
                    settingf='data/settings.ini')

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
