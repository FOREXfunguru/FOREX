import datetime
import pdb

def test_start(seg_pickled):
    assert datetime.datetime(2011, 2, 27, 22, 0) == seg_pickled.start()

def test_end(seg_pickled):
    assert datetime.datetime(2011, 3, 15, 21, 0) == seg_pickled.end()

def test_get_lowest(seg_pickled):
    assert datetime.datetime(2011, 3, 15, 21, 0) == seg_pickled.get_lowest().time

def test_get_highest(seg_pickled):
    assert datetime.datetime(2011, 2, 28, 22, 0) == seg_pickled.get_highest().time

def test_append(seg_pickled, seg_pickledB):
    assert len(seg_pickled.clist) == 17
    assert seg_pickled.diff == 346.8
    seg_pickled.append(seg_pickledB)
    assert len(seg_pickled.clist) == 60
    assert seg_pickled.diff == 743.1

def test_prepend(seg_pickled, seg_pickledB):
    assert len(seg_pickled.clist) == 17
    assert seg_pickled.diff == 346.8
    seg_pickled.prepend(seg_pickledB)
    assert len(seg_pickled.clist) == 60
    assert seg_pickled.diff == 35.7


