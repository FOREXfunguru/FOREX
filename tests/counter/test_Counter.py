from pattern.counter import Counter

import pytest
import datetime
import glob
import os
from trade_journal import Trade


@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('../data/IMGS/pivots/*')
    for f in files:
        os.remove(f)

@pytest.fixture
def ct_object():
    '''Returns Counter object'''

    t = Trade(
        id='EUR_GBP_13AUG2019D',
        start='2019-08-12 22:00:00',
        pair='EUR_GBP',
        timeframe='D',
        type='short',
        SR=0.92909,
        SL=0.93298,
        TP=0.90366,
        strat='counter_b1',
        settingf="data/settings.ini"
    )

    c = Counter(
        trade=t,
        settingf='data/settings.ini'
    )
    return c

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('../data/IMGS/pivots/*.png')
    for f in files:
        os.remove(f)

def test_clist_period(ct_object, clean_tmp):
    """
    Check that self.clist_period is correctly
    initialized with self.__initclist()
    """

    # check that the start datetime of clist_period
    # is correct
    assert datetime.datetime(2008, 8, 29, 21, 0) == ct_object.clist_period.clist[0].time

@pytest.mark.parametrize("start,"
                         "type,"
                         "SR,"
                         "SL,"
                         "TP,"
                         "entry,"
                         "lasttime",
                         [('2018-12-03 22:00:00', 'long', 1.54123, 1.53398, 1.55752, 1.54334,
                           datetime.datetime(2018, 6, 5, 21, 0)),
                          ('2018-09-11 22:00:00', 'short', 1.63118, 1.63633, 1.60202, 1.62763,
                           datetime.datetime(2009, 11, 29, 22, 0)),
                          ('2017-05-05 22:00:00', 'short', 1.48820, 1.49191, 1.46223, 1.48004,
                           datetime.datetime(2016, 9, 15, 21, 0)),
                          ('2019-05-23 22:00:00', 'short', 1.62344, 1.62682, 1.60294, 1.61739,
                           datetime.datetime(2018, 10, 4, 21, 0))])
def test_set_lasttime(start, type, SR, SL, TP, entry, lasttime, clean_tmp):
    """
    Check that self.lasttime class attribute
    has been initialized
    """
    t = Trade(
        id='test',
        start=start,
        pair='EUR_AUD',
        timeframe='D',
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        strat='counter_b1',
        settingf="data/settings.ini"
    )

    c = Counter(
        trade=t,
        period=1000,
        settingf='data/settings.ini'
    )
    c.set_lasttime()
    assert c.lasttime == lasttime


@pytest.mark.parametrize("pair,"
                         "timeframe,"
                         "id,"
                         "start,"
                         "type,"
                         "SR,"
                         "SL,"
                         "TP,"
                         "entry,"
                         "dates",
                         [  ('EUR_GBP', 'D', 'EUR_GBP 04JUN2004D', '2004-06-03 22:00:00', 'long', 0.66379, 0.66229, 0.67418,
                             0.66704, [datetime.datetime(2004, 6, 2, 21, 0)]),
                            ('EUR_JPY', 'D', 'EUR_JPY 04MAY2016D', '2016-05-03 22:00:00', 'long', 122.173, 121.57,
                             125.138, 123.021, [datetime.datetime(2008, 11, 3, 22, 0)]),
                            ('EUR_JPY', 'D', 'EUR_JPY 06APR2010D', '2010-04-05 22:00:00', 'short', 126.909, 128.151,
                            124.347, 126.627, [datetime.datetime(2008, 11, 3, 22, 0), datetime.datetime(2009, 3, 29, 21, 0),
                                               datetime.datetime(2009, 4, 26, 21, 0), datetime.datetime(2010, 4, 3, 21, 0)]),
                            ('EUR_JPY', 'D', 'EUR_JPY 27OCT2009D', '2009-10-26 22:00:00', 'short', 138.518, 138.66, 134.1, 136.852,
                            [datetime.datetime(2004, 3, 6, 22, 0), datetime.datetime(2005, 8, 7, 21, 0),
                             datetime.datetime(2006, 1, 11, 22, 0), datetime.datetime(2006, 2, 26, 22, 0),
                             datetime.datetime(2009, 6, 11, 21, 0), datetime.datetime(2009, 8, 8, 21, 0),
                             datetime.datetime(2009, 10, 24, 21, 0), datetime.datetime(2009, 10, 22, 21, 0)]),
                            ('EUR_JPY', 'D', 'EUR_JPY 15JUL2009D', '2009-07-14 22:00:00', 'long', 127.766, 126.421, 137.232, 130.865,
                            [datetime.datetime(2008, 11, 3, 22, 0), datetime.datetime(2009, 1, 3, 22, 0),
                             datetime.datetime(2009, 5, 16, 21, 0), datetime.datetime(2009, 7, 11, 21, 0)]),
                            ('NZD_USD', 'H12', 'NZD_USD 01JUL2019H12', '2019-07-01 09:00:00', 'short', 0.67095, 0.67258, 0.66328, 0.66887,
                            [datetime.datetime(2010, 5, 25, 21, 0), datetime.datetime(2010, 6, 6, 21, 0),
                             datetime.datetime(2016, 5, 29, 21, 0), datetime.datetime(2019, 1, 1, 22, 0),
                             datetime.datetime(2019, 6, 27, 21, 0)]),
                            ('EUR_AUD', 'D', 'EUR_AUD 04DEC2018D', '2018-12-03 22:00:00', 'long', 1.54123, 1.53398, 1.55752, 1.54334,
                            [datetime.datetime(2016, 1, 28, 22, 0), datetime.datetime(2018, 6, 3, 21, 0),
                             datetime.datetime(2018, 11, 29, 22, 0)]),
                            ('EUR_AUD', 'D', 'EUR_AUD 08MAY2017D', '2017-05-08 22:00:00', 'short', 1.48820, 1.49191, 1.46223, 1.48004,
                            [datetime.datetime(2010, 7, 1, 21, 0), datetime.datetime(2010, 7, 17, 21, 0),
                             datetime.datetime(2013, 8, 1, 21, 0), datetime.datetime(2015, 8, 3, 21, 0),
                             datetime.datetime(2017, 5, 7, 21, 0)]),
                           ('EUR_AUD', 'D', 'EUR_AUD 24MAY2019D', '2019-05-23 22:00:00', 'short', 1.62344, 1.62682, 1.60294, 1.61739,
                            [datetime.datetime(2008, 7, 15, 21, 0), datetime.datetime(2015, 8, 23, 21, 0),
                             datetime.datetime(2018, 12, 30, 22, 0), datetime.datetime(2019, 5, 21, 21, 0)]),
                           ('GBP_USD', 'D', 'GBP_USD 18APR2018D', '2018-04-17 22:00:00', 'short', 1.43690, 1.43778, 1.41005, 1.42681,
                           [datetime.datetime(2008, 12, 28, 22, 0), datetime.datetime(2009, 4, 21, 21, 0),
                           datetime.datetime(2010, 5, 17, 21, 0), datetime.datetime(2018, 4, 15, 21, 0)])])
def test_set_pivots(pair, id, timeframe, start, type, SR, SL, TP, entry, dates, clean_tmp):
    """
    Check that self.pivots class attribute
    """

    t = Trade(
        id=id,
        start=start,
        pair=pair,
        timeframe='D',
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        strat='counter_b1',
        settingf="data/settings.ini"
    )

    c = Counter(
        trade=t,
        settingf='data/settings.ini'
    )

    c.set_pivots()

    times = []
    for p in c.pivots.plist:
        times.append(p.candle.time)

    assert dates == times

def test_set_total_score(ct_object, clean_tmp):
    """
    Test 'set_total_score' function to set the 'total_score' class attr
    """
    ct_object.set_pivots()
    ct_object.set_total_score()
    assert ct_object.total_score == 509

@pytest.mark.parametrize("pair,"
                         "id,"
                         "start,"
                         "type,"
                         "SR,"
                         "SL,"
                         "TP,"
                         "entry,"
                         "dates",
                         [('EUR_AUD', 'EUR_AUD 04DEC2018D', '2018-12-03 22:00:00', 'long', 1.54123, 1.53398, 1.55752, 1.54334,
                          [datetime.datetime(2018, 11, 29, 22, 0)]),
                          ('EUR_AUD', 'EUR_AUD 08MAY2017D', '2017-05-08 22:00:00', 'short', 1.48820, 1.49191, 1.46223, 1.48004,
                           [datetime.datetime(2017, 5, 7, 21, 0)]),
                           ('EUR_AUD', 'EUR_AUD 24MAY2019D', '2019-05-23 22:00:00', 'short', 1.62344, 1.62682, 1.60294, 1.61739,
                           [datetime.datetime(2018, 12, 30, 22, 0), datetime.datetime(2019, 5, 21, 21, 0)]),
                           ('GBP_USD', 'GBP_USD 18APR2018D', '2018-04-17 22:00:00', 'short', 1.43690, 1.43778, 1.41005, 1.42681,
                           [datetime.datetime(2018, 4, 15, 21, 0)])])
def test_set_pivots_lasttime(pair, id, start, type, SR, SL, TP, entry, dates, clean_tmp):
    """
    Check that self.pivots_lasttime class attribute
    has been initialized
    """
    t = Trade(
        id=id,
        start=start,
        pair=pair,
        timeframe='D',
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        strat='counter_b1',
        settingf="data/settings.ini"
    )

    c = Counter(
        trade=t,
        period=1000,
        settingf='data/settings.ini'
    )

    c.set_lasttime()
    c.set_pivots()
    c.set_pivots_lasttime()

    times = []
    for p in c.pivots_lasttime.plist:
        times.append(p.candle.time)

    assert dates == times

def test_set_score_lasttime(ct_object, clean_tmp):
    '''Test 'set_score_lasttime' function to set the 'score_lasttime' class attr'''

    ct_object.set_lasttime()
    ct_object.set_pivots()
    ct_object.set_pivots_lasttime()
    ct_object.set_score_lasttime()

    assert ct_object.score_lasttime == 365

def test_set_score_pivot(ct_object, clean_tmp):
    ct_object.set_pivots()
    ct_object.set_total_score()
    ct_object.set_score_pivot()

    assert ct_object.score_pivot == 182.5

def test_set_score_pivot_lasttime(ct_object, clean_tmp):
    ct_object.set_pivots()
    ct_object.set_total_score()
    ct_object.set_lasttime()
    ct_object.set_pivots_lasttime()
    ct_object.set_score_lasttime()
    ct_object.set_score_pivot_lasttime()

    assert ct_object.score_pivot_lasttime == 182.5

"""
def test_calc_itrend(counter_object_notrendi):

    counter_object_notrendi.calc_itrend()


def test_set_slope(counter_object):

    counter_object.set_slope()

    assert counter_object.slope==0.0011973711767399185

def test_set_n_rsibounces(counter_object):

    counter_object.set_slope()
    counter_object.set_rsibounces_feats()

    assert counter_object.n_rsibounces==4
    assert counter_object.rsibounces_lengths[0]== 3
    assert counter_object.rsibounces_lengths[1]== 6

def test_set_divergence(counter_object):

    counter_object.set_slope()
    counter_object.set_divergence()

    assert counter_object.divergence==True

def test_set_entry_onrsi(counter_object):

    counter_object.set_entry_onrsi()

    assert counter_object.entry_onrsi==False

def test_set_length_candles(counter_object):

    counter_object.set_length_candles()

    assert counter_object.length_candles == 92

def test_set_length_pips(counter_object):

    counter_object.set_length_pips()

    assert counter_object.length_pips == 1259
"""