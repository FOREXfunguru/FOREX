import pytest
import logging
import pdb
import os

from oanda.connect import Connect
from candle.candlelist import CandleList
from trade_journal import TradeJournal

@pytest.fixture(autouse=True, scope="session")
def env_setup(monkeypatch):
    """
    Defining the environment
    """
    monkeypatch.setenv('DATADIR', '../data/')

@pytest.fixture
def clO(scope="session"):
    log = logging.getLogger('cl_object')
    log.debug('Create a CandleList object')

    conn = Connect(instrument='AUD_USD',
                   granularity='D',)

    res = conn.query(start='2019-03-06T23:00:00',
                   end='2020-01-24T23:00:00')

    cl = CandleList(res)
    return cl
