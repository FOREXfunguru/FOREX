import pytest
import logging
import pdb
import os
import glob

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
def clO():
    log = logging.getLogger('cl_object')
    log.debug('Create a CandleList object')

    alist = [
        {'complete': True,
        'volume': 8726, 
        'time': '2018-11-18T22:00:00',
        'o': '0.73093',
        'h': '0.73258',
        'l': '0.72776', 
        'c': '0.72950'},
        {'complete': True,
        'volume': 1000, 
        'time': '2018-11-19T22:00:00',
        'o': '0.70123',
        'h': '0.75123',
        'l': '0.68123', 
        'c': '0.72000'}
    ]
    cl = CandleList(instrument='AUD_USD',
                    granularity='D',
                    data=alist)
    return cl