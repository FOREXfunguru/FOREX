'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
import pytest
import pdb

from candle.candle import Candle
from oanda.connect import Connect

@pytest.fixture
def CandleO():
    '''
    Candle object instantiation
    '''
    a_dict = {'volume': 86555,
              'openBid': 1.42813,
              'complete': True,
              'time': '2018-04-17T21:00:00.000000Z',
              'closeBid': 1.41994,
              'lowBid': 1.41717,
              'highAsk': 1.43164,
              'highBid': 1.43143,
              'lowAsk': 1.41742,
              'closeAsk': 1.42075,
              'openAsk': 1.42903}
    c = Candle(dict_data=a_dict)

    return c

def test_set_candle_features(CandleO):
    '''
    Test function to set basic candle features based on price
    i.e. self.colour, upper_wick, etc...
    '''
    CandleO.set_candle_features()
    assert CandleO.colour == 'red'
    assert CandleO.upper_wick == 0.0033
    assert CandleO.lower_wick == 0.0028

@pytest.mark.parametrize("pair,"
                         "timeframe,"
                         "time,"
                         "is_it",
                         [('AUD_USD', 'D', '2020-03-18T22:00:00', True),
                          ('AUD_USD', 'D', '2019-07-31T22:00:00', False),
                          ('AUD_USD', 'D', '2019-03-19T22:00:00', False),
                          ('AUD_USD', 'D', '2020-01-22T22:00:00', True)])
def test_indecision_c(pair, timeframe, time, is_it):
    '''
    Test function to check if a certain Candle has the
    typical indecission pattern
    '''
    conn = Connect(instrument=pair,
                   granularity=timeframe)

    res = conn.query(start=time,
                     count=1)

    c_dict = res['candles'][0]

    cObj = Candle(dict_data=c_dict)


    cObj.set_candle_features()
    result = cObj.indecision_c()

    assert is_it == result

def test_volatile_c():
    '''
    Test for volatile_c function
    '''
    a_dict = {'volume': 18481,
              'openBid': 0.90822 ,
              'complete': True,
              'time': '2020-06-28T21:00:00.000000Z',
              'closeBid': 0.91386,
              'lowBid': 0.90793,
              'highAsk': 0.91765,
              'highBid': 0.91747,
              'lowAsk': 0.90858,
              'closeAsk': 0.9142,
              'openAsk': 0.90972}
    c = Candle(dict_data=a_dict)

    assert c.volatile_c(diff_cutoff=70, bit='Ask', pair='EUR_GBP') is True


