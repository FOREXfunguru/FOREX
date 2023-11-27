import pytest

from forex.candle import CandleList
from utils import DATA_DIR

@pytest.fixture
def clO_pickled():
    clO = CandleList.pickle_load(DATA_DIR+"/clist_audusd_2010_2020.pckl")
    clO.calc_rsi()

    return clO


@pytest.fixture
def clOH8_2019_pickled():
    clO = CandleList.pickle_load(DATA_DIR+"/clist.AUDUSD.H8.2019.pckl")
    clO.calc_rsi()

    return clO