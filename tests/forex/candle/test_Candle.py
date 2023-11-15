'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
import pytest
import pdb

from forex.candle import Candle

candle_feats = [
    ("2023-11-14T10:00:00", 0.87106, 0.87309, 0.87000, 0.87003),
    ("2018-11-14T14:00:00", 0.87003, 0.87104, 0.86890, 0.87035),
    ("2018-11-03T13:00:00", 0.86979, 0.87016, 0.86690, 0.86730)
]


@pytest.fixture
def CandleFactory():
    """Candle object factory"""
    candle_list = []
    for feats in candle_feats:
        candle_dict = {
              "time": feats[0],
              "o": feats[1],
              "h": feats[2],
              "l": feats[3],
              "c": feats[4]}
        candle_list.append(Candle(**candle_dict))
    return candle_list


@pytest.mark.parametrize("colour, perc_body", [
    (["red", "green", "red"], [33.33, 14.95, 76.38])
])
def test_check_candle_feats(CandleFactory, colour, perc_body):
    """Check that candle has the right attributes"""
    for ix in range(len(CandleFactory)):
        assert CandleFactory[ix].colour == colour[ix]
        assert CandleFactory[ix].perc_body == perc_body[ix]


@pytest.mark.parametrize("indecision_candle", [
    ([False, False, False])
])
def test_indecision_c(CandleFactory, indecision_candle):
    """Test function to check if a certain Candle has the
    typical indecission pattern"""

    for ix in range(len(CandleFactory)):
        assert CandleFactory[ix].indecision_c() is indecision_candle[ix]


@pytest.mark.parametrize("height", [
    ([30.9, 21.4, 32.6])
])
def test_height(CandleFactory, height):

    for ix in range(len(CandleFactory)):
        assert CandleFactory[ix].height(pair="EUR_GBP") == height[ix]
