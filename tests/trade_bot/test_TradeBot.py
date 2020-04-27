from trade_bot.trade_bot import TradeBot

import pytest
import glob
import os
import datetime

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('../data/IMGS/pivots/*')
    for f in files:
        os.remove(f)

@pytest.fixture
def tb_object():
    '''Returns TradeBot object'''
    tb = TradeBot(
        pair='EUR_GBP',
        timeframe='D',
        start='2019-08-12 22:00:00',
        end='2019-08-19 22:00:00',
        settingf="../../data/settings.ini"
    )
    return tb

def test_run(tb_object):
    """
    Check 'run' function
    """
    tb_object.run()

def test_run1():
    tb = TradeBot(
        pair='AUD_USD',
        timeframe='D',
        start='2018-01-02 22:00:00',
        end='2018-02-13 22:00:00',
        settingf="../../data/settings.ini")

    tl = tb.run()

    assert 0

def test_calc_SR(tb_object, clean_tmp):
    """
    Check 'calc_SR' function
    """
    harealst = tb_object.calc_SR()

    # check the length of HAreaList.halist
    assert len(harealst.halist) == 1

def test_calc_SR1(tb_object, clean_tmp):
    """
    Check 'calc_SR' function
    """
    harealst = tb_object.calc_SR(datetime.datetime(2017, 6, 13, 22, 0))

    # check the length of HAreaList.halist
    assert len(harealst.halist) == 1

def test_calc_SR2():
    """
    Check 'calc_SR' function for a H12 TradeBot
    """
    tb = TradeBot(
        pair='EUR_GBP',
        timeframe='H12',
        start='2017-06-11 22:00:00',
        end='2017-06-15 22:00:00',
        settingf="../../data/settings.ini"
    )

    harealst = tb.calc_SR(datetime.datetime(2017, 6, 13, 22, 0))

    # check the length of HAreaList.halist
    assert len(harealst.halist) == 4

def test_calc_SR3():
    """
    Check 'calc_SR' function for a H4 TradeBot
    """
    tb = TradeBot(
        pair='EUR_GBP',
        timeframe='H4',
        start='2017-06-11 22:00:00',
        end='2017-06-15 22:00:00',
        settingf="../../data/settings.ini"
    )

    harealst = tb.calc_SR(datetime.datetime(2017, 6, 13, 22, 0))

    # check the length of HAreaList.halist
    assert len(harealst.halist) == 4