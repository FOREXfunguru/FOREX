import pytest
import os
import glob
import pdb

from forex.candle import CandleList
from utils import DATA_DIR

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files1 = glob.glob(DATA_DIR+"/imgs/pivots/*")
    files2 = glob.glob(DATA_DIR+"/imgs/halist/*")
    files3 = glob.glob(DATA_DIR+"/imgs/srareas/*")
    files4 = glob.glob(DATA_DIR+"/imgs/pivots_report/*")

    files = files1 + files2 + files3 + files4
    for f in files:
        os.remove(f)

@pytest.fixture
def clO_pickled():
    return CandleList.pickle_load(DATA_DIR+"/clist_audusd_2010_2020.pckl")

