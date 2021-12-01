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
              'o': '0.73093',
              'h': '0.73258',
              'l': '0.72776', 
              'c': '0.72950'}

    c = Candle(**a_dict)

    return c

def test_check_candle_feats(CandleO):
    '''Check that candle has the right attributes'''
    assert CandleO.colour == 'red'
    assert CandleO.perc_body == 29.67

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