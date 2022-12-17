import pytest
import pdb

from forex.candle import CandleList
from forex.segment import Segment, SegmentList
from forex.pivot import PivotList
from utils import DATA_DIR

@pytest.fixture
def clO_pickled():
    return CandleList.pickle_load(DATA_DIR+"/clist_audusd_2010_2020.pckl")

@pytest.fixture
def seg_pickled():
    return Segment.pickle_load(DATA_DIR+"/seg_audusd.pckl")

@pytest.fixture
def seg_pickledB():
    return Segment.pickle_load(DATA_DIR+"/seg_audusdB.pckl")

@pytest.fixture
def seglist_pickled():
    return SegmentList.pickle_load(DATA_DIR+"/seglist_audusd.pckl")

@pytest.fixture
def pivotlist(clO_pickled):
    """Obtain a PivotList object"""
    return PivotList(clist=clO_pickled)






