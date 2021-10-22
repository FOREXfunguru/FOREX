'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
import pytest
import pdb

from forex.candle.candle import Candle
from api.oanda.connect import Connect

@pytest.fixture
def CandleO():
    '''Candle object instantiation.'''

    a_dict = {'complete': True,
              'volume': 8726, 
              'time': '2018-11-18T22:00:00.000000000Z',
              'mid': {'o': '0.73093',
                      'h': '0.73258',
                      'l': '0.72776', 
                      'c': '0.72950'}}

    c = Candle(**a_dict)

    return c

def test_set_candle_features(CandleO):
    '''Test function to set basic candle features based on price
    i.e. self.colour, upper_wick, etc...'''
    CandleO.set_candle_features()
    assert CandleO.colour == 'red'
    assert CandleO.upper_wick == 0.0017
    assert CandleO.lower_wick == 0.0017

@pytest.mark.parametrize("pair,"
                         "timeframe,"
                         "time,"
                         "is_it",
                         [('AUD_USD', 'D', '2020-03-18T22:00:00', True),
                          ('AUD_USD', 'D', '2019-07-31T22:00:00', False),
                          ('AUD_USD', 'D', '2019-03-19T22:00:00', False),
                          ('AUD_USD', 'D', '2020-01-22T22:00:00', True)])
def test_indecision_c(pair, timeframe, time, is_it):
    '''Test function to check if a certain Candle has the
    typical indecission pattern'''
    conn = Connect(instrument=pair,
                   granularity=timeframe)

    res = conn.query(start=time,
                     count=1)

    c_dict = res['candles'][0]
    cObj = Candle(**c_dict)
    cObj.set_candle_features()
    result = cObj.indecision_c()
    assert is_it == result

def test_volatile_c():
    '''Test for volatile_c function.'''

    a_dict = {'complete': True,
              'volume': 18481, 
              'time': '2020-06-28T21:00:00.000000Z',
              'mid': {'o': '0.90972',
                      'h': '0.91765',
                      'l': '0.90858', 
                      'c': '0.9142'}}

    c = Candle(**a_dict)

    assert c.volatile_c(diff_cutoff=70, bit='Ask', pair='EUR_GBP') is True


