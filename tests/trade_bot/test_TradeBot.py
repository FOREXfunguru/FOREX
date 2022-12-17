import pdb
import pytest
import datetime
import os
import logging

from trade_bot.trade_bot import TradeBot

# create logger
tb_logger = logging.getLogger(__name__)
tb_logger.setLevel(logging.DEBUG)

def test_run(tb_object, clean_tmp):
    """
    Check 'run' function with a TradeBot that does not
    return any trade
    """
    assert len(tb_object.run()) == 1

def test_run1(clean_tmp):
    """
    Test tradebot on a really easy to identify
    short trade on a tight time interval
    """
    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2018-01-22 22:00:00',
        end='2018-02-06 22:00:00')
    tl = tb.run()

    assert len(tl) == 3

def test_run_withclist(clO_pickled, clean_tmp):
    """
    Test tradebot using a pickled CandleList
    """
    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2018-01-22 22:00:00',
        end='2018-02-06 22:00:00',
        clist=clO_pickled)
    tl = tb.run()

    assert len(tl) == 3