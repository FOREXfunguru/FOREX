import pytest
import logging
import pdb
import os
import glob

from oanda.connect import Connect
from candle.candlelist import CandleList

@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """
    Defining the environment
    """
    monkeypatch.setenv('DATADIR', '../data/')

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files1 = glob.glob(os.getenv('DATADIR')+"/imgs/pivots/*")
    files2 = glob.glob(os.getenv('DATADIR')+"/imgs/halist/*")
    files3 = glob.glob(os.getenv('DATADIR')+"/imgs/srareas/*")
    files4 = glob.glob(os.getenv('DATADIR')+"/imgs/pivots_report/*")

    files = files1 + files2 + files3 + files4
    for f in files:
        os.remove(f)

@pytest.fixture
def clO(scope="session"):
    log = logging.getLogger('cl_object')
    log.debug('Create a CandleList object')

    conn = Connect(instrument='AUD_USD',
                   granularity='D')

    res = conn.query(start='2019-03-06T23:00:00',
                     end='2020-01-24T23:00:00')

    cl = CandleList(res)
    return cl
