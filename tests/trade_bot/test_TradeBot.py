import logging
import os
import pytest
import glob
import pickle

from params import tradebot_params, pivots_params
from trade_bot.trade_bot import TradeBot
from forex.candle import CandleList
from utils import DATA_DIR

# create logger
tb_logger = logging.getLogger(__name__)
tb_logger.setLevel(logging.DEBUG)


@pytest.fixture
def clO_pickled():
    clO = CandleList.pickle_load(DATA_DIR+"/clist_audusd_2010_2020.pckl")
    clO.calc_rsi()

    return clO


@pytest.fixture
def tb_object():
    tb = TradeBot(
            pair='EUR_GBP',
            timeframe='D',
            start='2020-06-29 22:00:00',
            end='2020-07-01 22:00:00')
    return tb


@pytest.fixture
def scan_pickled(clO_pickled, tmp_path):
    """Prepare a pickled file with potential trades identified by scan"""
    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2016-01-05 22:00:00',
        end='2016-02-11 22:00:00',
        clist=clO_pickled)
    prep_trades_list = tb.scan()
    with open(f"{tmp_path}/preptrades.pckl", "wb") as outfile:
        pickle.dump(prep_trades_list, outfile)
    return f"{tmp_path}/preptrades.pckl"


@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob(DATA_DIR+"/out/*")

    for f in files:
        os.remove(f)


def test_scan(tb_object, tmp_path):
    """Check the 'scan' function"""
    preptrade_list = tb_object.scan()
    assert len(preptrade_list) == 1


def test_scan1(tmp_path):
    """
    Test the scan() function with a certain TradeBot interval
    """
    pivots_params.th_bounces = 0.05
    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2016-01-05 22:00:00',
        end='2016-02-11 22:00:00')
    preptrade_list = tb.scan()
    assert len(preptrade_list) == 5


def test_scan_withclist(clO_pickled, tmp_path):
    """
    Test the scan() method using a pickled CandleList
    """
    pivots_params.th_bounces = 0.05
    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2016-01-05 22:00:00',
        end='2016-02-11 22:00:00',
        clist=clO_pickled)
    preptrade_list = tb.scan()
    assert len(preptrade_list) == 5


def test_scan_withclist_future(clO_pickled, tmp_path):
    """
    Test tradebot using a pickled CandleList and using an end TradeBot time
    post clO_pickled end time. This scan() invokation will not return any
    preTrade
    """

    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2020-11-15 22:00:00',
        end='2020-11-23 22:00:00',
        clist=clO_pickled)
    preptrade_list = tb.scan()
    assert len(preptrade_list) == 0


def test_prepare_trades(clO_pickled, scan_pickled):
    """
    Test the prepare_trades() method with a pickled list
    of preTrade objects
    """
    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2016-01-05 22:00:00',
        end='2016-02-11 22:00:00',
        clist=clO_pickled)
    tl = tb.prepare_trades(pretrades=scan_pickled)
    assert len(tl) == 5 or len(tl) == 4


def test_prepare_trades_nextSR(clO_pickled,
                               scan_pickled):
    """
    Test tradebot using a pickled CandleList and
      tradebot_params.adj_SL = 'nextSR'
    """
    tradebot_params.adj_SL = 'nextSR'

    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2016-01-05 22:00:00',
        end='2016-02-11 22:00:00',
        clist=clO_pickled)
    tl = tb.prepare_trades(pretrades=scan_pickled)
    assert len(tl) == 5 or len(tl) == 4


def test_prepare_trades_pips(clO_pickled,
                             scan_pickled):
    """
    Test tradebot using a pickled CandleList and
      tradebot_params.adj_SL = 'pips'
    """
    tradebot_params.adj_SL = "pips"

    tb = TradeBot(
        pair="AUD_USD",
        timeframe="D",
        start="2016-01-05 22:00:00",
        end="2016-02-11 22:00:00",
        clist=clO_pickled)
    tl = tb.prepare_trades(pretrades=scan_pickled)
    assert len(tl) == 5 or len(tl) == 4
