from tradebot import TradeBot

import pytest
import pdb
import glob
import os

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('data/IMGS/pivots/*')
    for f in files:
        os.remove(f)

@pytest.fixture
def tb_object():
    '''Returns TradeBot object'''
    tb = TradeBot(
        pair='EUR_GBP',
        timeframe='D',
        settingf="data/settings.ini"
    )
    return tb

def test_run(tb_object):
    """
    Check 'run' function
    """
    tb_object.run(start='2019-08-12T22:00:00',
                  end='2019-08-19T22:00:00')

def test_calc_SR(tb_object):
    """

    :param tb_object:
    :return:
    """