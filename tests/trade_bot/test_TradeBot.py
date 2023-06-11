import logging
import os
import pytest

from params import tradebot_params, pivots_params
from trade_bot.trade_bot import TradeBot
from utils import DATA_DIR

# create logger
tb_logger = logging.getLogger(__name__)
tb_logger.setLevel(logging.DEBUG)


@pytest.fixture
def scan_pickled(clO_pickled):
    """Prepare a pickled file with potential trades identified by scan"""
    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2016-01-05 22:00:00',
        end='2016-02-11 22:00:00',
        clist=clO_pickled)
    outfile = tb.scan(prefix=f"{DATA_DIR}/out/test_scan")
    return outfile


def test_scan(tb_object, clean_tmp):
    """Check the 'scan' function"""
    outfile = tb_object.scan(prefix=f"{DATA_DIR}/out/test_scan")
    assert os.path.isfile(outfile)


def test_scan1(clean_tmp):
    """
    Test the scan() function with a certain TradeBot interval
    """
    pivots_params.th_bounces = 0.05
    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2016-01-05 22:00:00',
        end='2016-02-11 22:00:00')
    outfile = tb.scan(prefix=f"{DATA_DIR}/out/test_scan")
    assert os.path.isfile(outfile)


def test_scan_withclist(clO_pickled, clean_tmp):
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
    outfile = tb.scan(prefix=f"{DATA_DIR}/out/test_scan")
    assert os.path.isfile(outfile)


def test_scan_withclist_future(clO_pickled, clean_tmp):
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
    outfile = tb.scan(prefix=f"{DATA_DIR}/out/test_scan")
    with pytest.raises(TypeError):
        assert os.path.isfile(outfile)


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


def test_run_withclist_nextSR(clO_pickled, scan_pickled, clean_tmp):
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
