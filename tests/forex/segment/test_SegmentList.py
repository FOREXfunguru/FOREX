import datetime

def test_calc_diff(seglist_pickled):

    seglist_pickled.calc_diff()

    assert seglist_pickled.diff == 2513.6

def test_length_cl(seglist_pickled):

    assert seglist_pickled.length_cl() == 2801

def test_start(seglist_pickled):

    assert seglist_pickled.start() == datetime.datetime(2010, 11, 16, 22, 0)

def test_end(seglist_pickled):

    assert seglist_pickled.end() == datetime.datetime(2020, 11, 18, 22, 0)

def test_fetch_by_start(seglist_pickled):

    adt = datetime.datetime(2019, 4, 16, 21, 0)
    s = seglist_pickled.fetch_by_start(adt)

    assert s.start() == adt

def test_fetch_by_end(seglist_pickled):
    """Test fetch_by_end"""

    adt = datetime.datetime(2019, 6, 13, 21, 0)

    s = seglist_pickled.fetch_by_end(adt)

    assert s.end() == adt
