import pytest
import pdb

from OandaAPI import OandaAPI
from CandleList import CandleList

@pytest.fixture
def oanda_object():
    '''Returns an  oanda object'''

    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument='AUD_USD',
                   granularity='D',
                   alignmentTimezone='Europe/London',
                   dailyAlignment=22,
                   start='2015-01-26T22:00:00',
                   end='2015-01-29T22:00:00')

    return oanda


def test_CandleList():
    '''
    Test the creation of a CandleList object

    '''
    # time must be in a valid datetime format
    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument='AUD_USD',
                   granularity='D',
                   alignmentTimezone='Europe/London',
                   start='2015-01-25T22:00:00',
                   end='2015-01-26T22:00:00')

    candle_list=oanda.fetch_candleset()

    cl=CandleList(candle_list, type='long')

    one_c=cl.next()
    assert one_c.highBid==0.79328
    assert one_c.openBid==0.7873
    assert one_c.lowBid==0.7857
    assert one_c.representation=='bidask'
    assert one_c.lowAsk==0.786
    assert one_c.complete==True
    assert one_c.openAsk==0.7889
    assert one_c.highAsk==0.79345
    assert one_c.highBid==0.79328
    assert one_c.volume==11612
    assert one_c.closeBid==0.79316
    assert one_c.closeAsk==0.79335
    assert one_c.openBid==0.7873

def get_dictionary(k, v):
    d = dict([x, ord(x)] for x in  string.printable)
    d[k] = v
    return d

'''
def test_calc_binary_seq(oanda_object):
    
    candle_list=oanda_object.fetch_candleset()

    cl=CandleList(candle_list, type='short')

    cl.calc_binary_seq(merge=False)
    dict1=cl.seq
    dict2={'open': '01', 'colour': '011', 'high': '01', 'close': '11', 'low': '11'}

    shared_items = set(dict1.items()) & set(dict2.items())

    assert len(shared_items) == 5
'''

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
