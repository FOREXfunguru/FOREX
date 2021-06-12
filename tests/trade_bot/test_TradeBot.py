import pdb
import pytest
import datetime
import os
import logging

from trade_bot.trade_bot import TradeBot
from config import CONFIG

# create logger
tb_logger = logging.getLogger(__name__)
tb_logger.setLevel(logging.DEBUG)

def test_run(tb_object, clean_tmp):
    """
    Check 'run' function with a TradeBot that does not
    return any trade
    """
    assert len(tb_object.run()) == 1

def test_run1():
    """
    Test tradebot on a really easy to identify
    short trade on a tight time interval
    """

    CONFIG.set('trade_bot', 'period_range', '1500')

    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2018-01-22 22:00:00',
        end='2018-02-06 22:00:00')

    tl = tb.run()

    assert len(tl.tlist) == 2

def test_run2(clean_tmp):
    """
    Test tradebot on a really easy to identify
    long trade on a tight time interval
    """
    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2012-05-24 22:00:00',
        end='2012-06-06 22:00:00',
        settingf="../../data/settings.ini")

    tl = tb.run()

    assert len(tl.tlist) == 1

def test_run3(clean_tmp):
    """
    Test tradebot on a really easy to identify
    short trade on a tight time interval using
    USD_JPY
    """
    tb = TradeBot(
        pair='USD_JPY',
        timeframe='D',
        start='2018-09-24 22:00:00',
        end='2018-10-09 22:00:00',
        settingf="../../data/settings.ini")

    tl = tb.run()

    assert len(tl.tlist) == 1

def test_run4(clean_tmp):
    """
    Test tradebot on a possible trade that falls on a
    Saturday and will not be taken
    """
    tb = TradeBot(
        pair='AUD_JPY',
        timeframe='D',
        start='2008-12-30 22:00:00',
        end='2009-01-06 22:00:00',
        settingf="../../data/settings.ini")

    tl = tb.run()

    assert tl is None

@pytest.mark.parametrize("pair,"
                         "start,"
                         "end,"
                         "len_tl",
                         [('GBP_USD', '2019-11-07 02:00:00', '2019-11-12 10:00:00', 1),
                          ('AUD_USD', '2018-04-30 21:00:00', '2018-05-02 17:00:00', 1)])
def test_run_H4(pair, start, end, len_tl, settings_obj, clean_tmp):
    """
    Test tradebot using an H4 timeframe
    """
    settings_obj.set('pivots', 'th_bounces', '0.01')
    settings_obj.set('trade_bot', 'th', '0.2')
    settings_obj.set('trade_bot', 'period_range', '6000')

    tb = TradeBot(
        pair=pair,
        timeframe='H4',
        start=start,
        end=end,
        settings=settings_obj)

    tl = tb.run()

    assert len(tl.tlist) == len_tl

@pytest.mark.parametrize("pair,"
                         "start,"
                         "end,"
                         "len_tl",
                         [('GBP_USD', '2018-08-27 13:00:00', '2018-09-03 21:00:00', 1)])
def test_run_H8(pair, start, end, len_tl, settings_obj, clean_tmp):
    """
    Test tradebot using an H4 timeframe
    """

    settings_obj.set('pivots', 'th_bounces', '0.02')
    settings_obj.set('trade_bot', 'th', '0.2')
    settings_obj.set('trade_bot', 'period_range', '4500')

    tb = TradeBot(
        pair=pair,
        timeframe='H8',
        start=start,
        end=end,
        settings=settings_obj)

    tl = tb.run()

    assert len(tl.tlist) == len_tl

@pytest.mark.parametrize("pair,"
                         "start,"
                         "end,"
                         "len_tl",
                         [('USD_JPY', '2018-09-27 09:00:00', '2018-10-09 21:00:00', 1)])
def test_run_H12(pair, start, end, len_tl, settings_obj, clean_tmp):
    """
    Test tradebot using an H4 timeframe
    """

    settings_obj.set('pivots', 'th_bounces', '0.02')
    settings_obj.set('trade_bot', 'th', '0.6')
    settings_obj.set('trade_bot', 'period_range', '3500')

    tb = TradeBot(
        pair=pair,
        timeframe='H12',
        start=start,
        end=end,
        settings=settings_obj)

    tl = tb.run()

    assert len(tl.tlist) == len_tl


@pytest.mark.parametrize("pair,"
                         "start,"
                         "end,"
                         "adatetime,"
                         "halen",
                         [('AUD_USD', '2017-02-28 22:00:00', '2017-03-23 13:00:00', '2017-03-14 13:00:00', 8),
                          ('AUD_USD', '2019-07-17 13:00:00', '2019-07-23 13:00:00', '2019-07-19 05:00:00', 3)])
def test_calc_SR_8hrs(pair, start, end, adatetime, halen, settings_obj, clean_tmp):
    """
    Check 'calc_SR' function for a H8 timeframe
    """
    settings_obj.set('pivots', 'th_bounces', '0.02')
    settings_obj.set('trade_bot', 'th', '0.2')
    settings_obj.set('trade_bot', 'period_range', '4500')

    adatetimeObj = datetime.datetime.strptime(adatetime, "%Y-%m-%d %H:%M:%S")

    tb = TradeBot(
        pair=pair,
        timeframe='H8',
        start=start,
        end=end,
        settings=settings_obj)

    harealst = tb.calc_SR(adatetimeObj)

    assert len(harealst.halist) == halen

@pytest.mark.parametrize("pair,"
                         "start,"
                         "end,"
                         "adatetime,"
                         "halen",
                         [('USD_JPY', '2018-05-25 09:00:00', '2018-06-04 21:00:00', '2018-05-30 21:00:00', 8)])
def test_calc_SR_H12hrs(pair, start, end, adatetime, halen, settings_obj, clean_tmp):
    """
    Check 'calc_SR' function for a H12 timeframe
    """
    settings_obj.set('pivots', 'th_bounces', '0.02')
    settings_obj.set('trade_bot', 'th', '0.6')
    settings_obj.set('trade_bot', 'period_range', '3500')

    adatetimeObj = datetime.datetime.strptime(adatetime, "%Y-%m-%d %H:%M:%S")

    tb = TradeBot(
        pair=pair,
        timeframe='H12',
        start=start,
        end=end,
        settings=settings_obj)

    harealst = tb.calc_SR(adatetimeObj)

    assert len(harealst.halist) == halen
