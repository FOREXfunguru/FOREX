'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
import pytest
import pdb

from forex.candle import Candle

candle_feats = [
    ('2018-11-18T22:00:00', 0.73093, 0.73258, 0.72776, 0.72950)
]


@pytest.fixture
def CandleFactory():
    """Candle object factory"""
    for feats in candle_feats:
        candle_dict = {
              'time': '2018-11-18T22:00:00',
              'o': '0.73093',
              'h': '0.73258',
              'l': '0.72776',
              'c': '0.72950'}

    c = Candle(**a_dict)

    return c


def test_check_candle_feats(CandleFactory):
    '''Check that candle has the right attributes'''
    assert CandleO.colour == 'red'
    assert CandleO.perc_body == 29.67


def test_indecision_c(CandleFactory):
    '''Test function to check if a certain Candle has the
    typical indecission pattern'''

    for candle in CandleFactory:
        assert candle.indecision_c() is False


def test_height(CandleO):

    assert 48.2 == CandleO.height(pair="AUD_USD")
