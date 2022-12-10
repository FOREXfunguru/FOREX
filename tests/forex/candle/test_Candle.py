'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
import pytest
import pdb

from forex.candle import Candle

@pytest.fixture
def CandleO():
    '''Candle object instantiation.'''
    a_dict = {'complete': True,
              'volume': 8726, 
              'time': '2018-11-18T22:00:00',
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


def test_indecision_c(CandleO):
    '''Test function to check if a certain Candle has the
    typical indecission pattern'''

    assert False == CandleO.indecision_c()