import pytest
import logging
import pdb
import os
import glob

from api.oanda.connect import Connect
from forex.candle.candlelist import CandleList
from utils import DATA_DIR

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files1 = glob.glob(DATA_DIR+"/imgs/pivots/*")
    files2 = glob.glob(DATA_DIR+"/imgs/halist/*")
    files3 = glob.glob(DATA_DIR+"/imgs/srareas/*")
    files = files1 + files2 + files3
    for f in files:
        os.remove(f)

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
