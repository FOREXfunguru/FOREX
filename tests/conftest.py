import pytest
import glob
import os

from trading_journal.trade import Trade
from trading_journal.trade_journal import TradeJournal
from forex.candle import CandleList
from utils import DATA_DIR

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files1 = glob.glob(DATA_DIR+"/imgs/pivots/*")
    files2 = glob.glob(DATA_DIR+"/imgs/halist/*")
    files3 = glob.glob(DATA_DIR+"/imgs/srareas/*")
    files4 = glob.glob(DATA_DIR+"/out/*.pckl")
    files5 = glob.glob(DATA_DIR+"/out/*.png")

    files = files1 + files2 + files3 + files4 +files5
    for f in files:
        os.remove(f)

@pytest.fixture
def clO_pickled():
    clO = CandleList.pickle_load(DATA_DIR+"/clist_audusd_2010_2020.pckl")
    clO.calc_rsi()

    return clO

@pytest.fixture
def t_object(clO_pickled):
    '''Returns a Trade object'''

    td = Trade(
        start="2017-04-10 14:00:00",
        end="2017-04-26 14:00:00",
        entry=0.74960,
        TP=0.75592,
        SL=0.74718,
        SR=0.74784,
        pair="AUD_USD",
        type="long",
        timeframe="D",
        clist=clO_pickled)
    return td

@pytest.fixture
def t_object_list(scope="session"):
    '''Returns a list of Trade objects'''

    td = Trade(
        start="2017-04-10 14:00:00",
        end="2017-04-26 14:00:00",
        entry=0.74960,
        TP=0.75592,
        SL=0.74718,
        SR=0.74784,
        pair="AUD_USD",
        type="long",
        timeframe="H8",
        strat="counter_b1",
        id="AUD_USD 10APR2017H8")
    return [td]

@pytest.fixture
def tjO(scope="session"):
    '''Returns a trade_journal object for a Counter trade'''
    td = TradeJournal(url=DATA_DIR+"/testCounter.xlsx",
                      worksheet="trading_journal")
    return td
