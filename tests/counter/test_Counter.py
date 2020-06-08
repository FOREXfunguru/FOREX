from pattern.counter import Counter

import pytest
import datetime
import glob
import os
import pdb

from trade_journal.trade import Trade
from configparser import ConfigParser


@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('../../data/IMGS/pivots/*')
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
        settingf="../../data/settings.ini"
    )

    c = Counter(
        trade=t,
        settingf='../../data/settings.ini'
    )
    return c

@pytest.fixture
def settings_obj():
    """
    This fixture returns a ConfigParser
    object with settings
    """
    parser = ConfigParser()
    parser.read("../../data/settings.ini")

    return parser

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('../../data/IMGS/pivots/*.png')
    for f in files:
        os.remove(f)

@pytest.mark.parametrize("start,"
                         "SR,"
                         "SL,"
                         "TP,"
                         "entry",
                         [('2018-12-03 22:00:00', 1.54123, 1.53398, 1.55752, 1.54334)])
def test_ctobject_notype(start, SR, SL, TP, entry, clean_tmp):
    """
    Check that Counter object without
    a type defined is correctly instantiated
    """
    t = Trade(
        id='test',
        start=start,
        pair='EUR_AUD',
        timeframe='D',
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        strat='counter_b1',
        settingf="../../data/settings.ini"
    )

    c = Counter(
        trade=t,
        period=1000,
        settingf='../../data/settings.ini')

    assert 0

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
                           datetime.datetime(2018, 1, 8, 22, 0)),
                          ('2018-09-11 22:00:00', 'short', 1.63118, 1.63633, 1.60202, 1.62763,
                           datetime.datetime(2009, 11, 27, 22, 0)),
                          ('2017-05-05 22:00:00', 'short', 1.48820, 1.49191, 1.46223, 1.48004,
                           datetime.datetime(2016, 9, 13, 21, 0)),
                          ('2019-05-23 22:00:00', 'short', 1.62344, 1.62682, 1.60294, 1.61739,
                           datetime.datetime(2009, 11, 29, 22, 0))])
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
        settingf="../../data/settings.ini"
    )

    c = Counter(
        trade=t,
        period=1000,
        settingf='../../data/settings.ini')

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
                         [  ('EUR_GBP', 'D', 'EUR_GBP 28JAN2007D', '2007-01-27 22:00:00', 'long', 0.6595, 0.65376, 0.6691,
                              0.65989, [datetime.datetime(2004, 6, 9, 21, 0), datetime.datetime(2004, 8, 1, 21, 0),
                                        datetime.datetime(2005, 6, 23, 21, 0), datetime.datetime(2007, 1, 28, 22, 0)]),
                             ('EUR_GBP', 'D', 'EUR_GBP 22MAY2007D', '2007-05-21 21:00:00', 'short', 0.6833, 0.68584, 0.6771,
                              0.68235, [datetime.datetime(2003, 11, 2, 22, 0), datetime.datetime(2004, 3, 10, 22, 0),
                                        datetime.datetime(2004, 12, 16, 22, 0)]),
                             ('EUR_GBP', 'D', 'EUR_GBP 04JUN2004D', '2004-06-03 22:00:00', 'long', 0.66379, 0.66229, 0.67418,
                             0.66704, [datetime.datetime(2004, 6, 2, 21, 0)]),
                            ('EUR_JPY', 'D', 'EUR_JPY 04MAY2016D', '2016-05-03 22:00:00', 'long', 122.173, 121.57,
                             125.138, 123.021, [datetime.datetime(2009, 1, 17, 22, 0), datetime.datetime(2016, 2, 28, 22, 0), datetime.datetime(2016, 5, 2, 21, 0)]),
                            ('EUR_JPY', 'D', 'EUR_JPY 06APR2010D', '2010-04-05 22:00:00', 'short', 126.909, 128.151,
                            124.347, 126.627, [datetime.datetime(2009, 3, 29, 21, 0), datetime.datetime(2010, 4, 3, 21, 0)]),
                            ('EUR_JPY', 'D', 'EUR_JPY 27OCT2009D', '2009-10-26 22:00:00', 'short', 138.518, 138.66, 134.1, 136.852,
                            [datetime.datetime(2004, 3, 6, 22, 0), datetime.datetime(2005, 8, 7, 21, 0),
                             datetime.datetime(2009, 6, 11, 21, 0), datetime.datetime(2009, 8, 8, 21, 0),
                             datetime.datetime(2009, 10, 24, 21, 0), datetime.datetime(2009, 10, 22, 21, 0)]),
                            ('EUR_JPY', 'D', 'EUR_JPY 15JUL2009D', '2009-07-14 22:00:00', 'long', 127.766, 126.421, 137.232, 130.865,
                            [datetime.datetime(2009, 1, 3, 22, 0), datetime.datetime(2009, 5, 16, 21, 0),
                             datetime.datetime(2009, 7, 11, 21, 0)]),
                            ('NZD_USD', 'H12', 'NZD_USD 01JUL2019H12', '2019-07-01 09:00:00', 'short', 0.67095, 0.67258, 0.66328, 0.66887,
                            [datetime.datetime(2016, 5, 29, 21, 0), datetime.datetime(2019, 1, 1, 22, 0),
                             datetime.datetime(2019, 6, 27, 21, 0)]),
                            ('EUR_AUD', 'D', 'EUR_AUD 04DEC2018D', '2018-12-03 22:00:00', 'long', 1.54123, 1.53398, 1.55752, 1.54334,
                            [datetime.datetime(2018, 11, 29, 22, 0)]),
                            ('EUR_AUD', 'D', 'EUR_AUD 08MAY2017D', '2017-05-08 22:00:00', 'short', 1.48820, 1.49191, 1.46223, 1.48004,
                            [datetime.datetime(2010, 7, 17, 21, 0), datetime.datetime(2013, 8, 1, 21, 0),
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
        settingf="../../data/settings.ini"
    )

    c = Counter(trade=t,
                settingf='../../data/settings.ini')

    c.set_pivots()

    times = []
    for p in c.pivots.plist:
        times.append(p.candle.time)

    assert dates == times

@pytest.mark.parametrize("pair,"
                         "timeframe,"
                         "id,"
                         "start,"
                         "type,"
                         "SR,"
                         "SL,"
                         "TP,"
                         "entry,"
                         "pllen",
                         [('EUR_GBP', 'H4', 'EUR_GBP 19FEB2020H4', '2020-02-19 06:00:00', 'long', 0.82920, 0.82793, 0.83801,
                             0.83196, 2),
                          ('EUR_GBP', 'H4', 'EUR_GBP 06MAY2019H4', '2019-05-06 01:00:00', 'long', 0.85036, 0.84874, 0.85763,
                             0.85109, 2),
                          ('EUR_GBP', 'H4', 'EUR_GBP 07FEB2018H4', '2018-02-07 14:00:00', 'short', 0.89099, 0.89115, 0.87867,
                             0.88621, 8)])
def test_set_pivots_4h(pair, timeframe, id, start, type, SR, SL, TP, entry, pllen, settings_obj, clean_tmp):
    """
    Check that self.pivots class attribute is correctly set using a H4 timeframe
    """

    settings_obj.set('pivots', 'th_bounces', '0.01')

    t = Trade(
        id=id,
        start=start,
        pair=pair,
        timeframe=timeframe,
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        strat='counter_b1',
        settings=settings_obj
    )

    c = Counter(
        trade=t,
        settings=settings_obj)

    c.set_pivots()

    assert len(c.pivots.plist) == pllen

@pytest.mark.parametrize("pair,"
                         "timeframe,"
                         "id,"
                         "start,"
                         "type,"
                         "SR,"
                         "SL,"
                         "TP,"
                         "entry,"
                         "trend_i",
                         [
                          ('AUD_JPY', 'D', 'AUD_JPY 16MAR2010D', '2010-03-15 21:00:00', 'short', 82.63, 83.645, 80.32, 82.315,
                           datetime.datetime(2010, 2, 4, 22, 0)),
                          ('AUD_CAD', 'D', 'AUD_CAD 01JAN2020D', '2019-12-31 22:00:00', 'short', 0.9149, 0.91574, 0.9019,
                           0.91574, datetime.datetime(2019, 10, 1, 21, 0)),
                          ('EUR_GBP', 'D', 'EUR_GBP 23FEB2007D', '2007-02-22 22:00:00', 'short', 0.6713, 0.6758, 0.6615,
                           0.67009, datetime.datetime(2007, 1, 22, 22, 0)),
                          ('EUR_GBP', 'D', 'EUR_GBP 04JUN2004D', '2004-06-03 22:00:00', 'long', 0.66379, 0.66229, 0.67418,
                           0.66704, datetime.datetime(2004, 5, 16, 21, 0)),
                          ('EUR_JPY', 'D', 'EUR_JPY 04MAY2016D', '2016-05-03 22:00:00', 'long', 122.173, 121.57,
                           125.138, 123.021, datetime.datetime(2016, 4, 26, 21, 0)),
                          ('EUR_JPY', 'D', 'EUR_JPY 06APR2010D', '2010-04-05 22:00:00', 'short', 126.909, 128.151,
                           124.347, 126.627, datetime.datetime(2010, 3, 23, 21, 0)),
                          ('EUR_JPY', 'D', 'EUR_JPY 27OCT2009D', '2009-10-26 22:00:00', 'short', 138.518, 138.66, 134.1, 136.852,
                           datetime.datetime(2009, 10, 6, 21, 0)),
                          ('EUR_JPY', 'D', 'EUR_JPY 15JUL2009D', '2009-07-14 22:00:00', 'long', 127.766, 126.421, 137.232, 130.865,
                           datetime.datetime(2009, 6, 11, 21, 0)),
                          ('NZD_USD', 'H12', 'NZD_USD 01JUL2019H12', '2019-07-01 09:00:00', 'short', 0.67095, 0.67258, 0.66328, 0.66887,
                           datetime.datetime(2019, 6, 14, 9, 0)),
                          ('EUR_AUD', 'D', 'EUR_AUD 04DEC2018D', '2018-12-03 22:00:00', 'long', 1.54123, 1.53398, 1.55752, 1.54334,
                           datetime.datetime(2018, 10, 4, 21, 0)),
                          ('EUR_AUD', 'D', 'EUR_AUD 08MAY2017D', '2017-05-08 22:00:00', 'short', 1.48820, 1.49191, 1.46223, 1.48004,
                           datetime.datetime(2017, 2, 21, 22, 0)),
                          ('EUR_AUD', 'D', 'EUR_AUD 24MAY2019D', '2019-05-23 22:00:00', 'short', 1.62344, 1.62682, 1.60294, 1.61739,
                           datetime.datetime(2019, 4, 17, 21, 0)),
                          ('GBP_USD', 'D', 'GBP_USD 18APR2018D', '2018-04-17 22:00:00', 'short', 1.43690, 1.43778, 1.41005, 1.42681,
                           datetime.datetime(2018, 2, 28, 22, 0))])
def test_set_trend_i(pair, id, timeframe, start, type, SR, SL, TP, entry, trend_i, clean_tmp):
    t = Trade(
        id=id,
        start=start,
        pair=pair,
        timeframe=timeframe,
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        strat='counter_b1',
        settingf="../../data/settings.ini")

    c = Counter(
        trade=t,
        settingf='../../data/settings.ini')

    c.set_trend_i()
    assert trend_i == c.trend_i

@pytest.mark.parametrize("pair,"
                         "timeframe,"
                         "id,"
                         "start,"
                         "type,"
                         "SR,"
                         "SL,"
                         "TP,"
                         "entry,"
                         "pips_c_trend",
                         [('AUD_JPY', 'D', 'AUD_JPY 09FEB2010D', '2010-02-08 22:00:00', 'long', 76.820, 76.094, 80.289, 77.764,
                           24.1),
                          ('AUD_JPY', 'D', 'AUD_JPY 16MAR2010D', '2010-03-15 21:00:00', 'short', 82.63, 83.645, 80.32, 82.315,
                           13.4)])
def test_set_pips_c_trend(pair, id, timeframe, start, type, SR, SL, TP, entry, pips_c_trend, clean_tmp):
    t = Trade(
        id=id,
        start=start,
        pair=pair,
        timeframe=timeframe,
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        strat='counter_b1',
        settingf="../../data/settings.ini"
    )

    c = Counter(trade=t,
                settingf='../../data/settings.ini',
                init_feats=True)

    assert pips_c_trend == c.pips_c_trend

@pytest.mark.parametrize("pair,"
                         "timeframe,"
                         "id,"
                         "start,"
                         "type,"
                         "SR,"
                         "SL,"
                         "TP,"
                         "entry,"
                         "entry_onrsi",
                         [('EUR_GBP', 'D', 'EUR_GBP 23FEB2007D', '2007-02-22 22:00:00', 'short', 0.6713, 0.6758, 0.6615,
                           0.67009, False),
                          ('EUR_JPY', 'D', 'EUR_JPY 04MAY2016D', '2016-05-03 22:00:00', 'long', 122.173, 121.57,
                           125.138, 123.021, False),
                          ('EUR_JPY', 'D', 'EUR_JPY 06APR2010D', '2010-04-05 22:00:00', 'short', 126.909, 128.151,
                           124.347, 126.627, False),
                          ('EUR_JPY', 'D', 'EUR_JPY 27OCT2009D', '2009-10-26 22:00:00', 'short', 138.518, 138.66, 134.1, 136.852,
                           False),
                          ('EUR_JPY', 'H8', 'EUR_JPY 21OCT2009H8', '2009-10-21 13:00:00', 'short', 121.055, 121.517, 120.166, 121.517,
                           True),
                          ('EUR_JPY', 'H8', 'EUR_JPY 04JUN2020H8', '2020-06-04 21:00:00', 'short', 124.058, 124.478, 121.648,
                           123.655, True)])
def test_is_entry_onrsi(pair, id, timeframe, start, type, SR, SL, TP, entry, entry_onrsi, clean_tmp):
    t = Trade(
        id=id,
        start=start,
        pair=pair,
        timeframe=timeframe,
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        strat='counter_b1',
        settingf="../../data/settings.ini"
    )

    c = Counter(
        trade=t,
        settingf='../../data/settings.ini',
        init_feats=True
    )

    assert entry_onrsi == c.is_entry_onrsi()
    assert 0

@pytest.mark.parametrize("pair,"
                         "timeframe,"
                         "id,"
                         "start,"
                         "type,"
                         "SR,"
                         "SL,"
                         "TP,"
                         "entry,"
                         "avalue",
                         [('EUR_GBP', 'D', 'EUR_GBP 23FEB2007D', '2007-02-22 22:00:00', 'short', 0.6713, 0.6758, 0.6615,
                           0.67009, 66.0),
                          ('EUR_GBP', 'D', 'EUR_GBP 04JUN2004D', '2004-06-03 22:00:00', 'long', 0.66379, 0.66229, 0.67418,
                           0.66704, 39.31),
                          ('EUR_JPY', 'D', 'EUR_JPY 04MAY2016D', '2016-05-03 22:00:00', 'long', 122.173, 121.57,
                           125.138, 123.021, 33.09),
                          ('EUR_JPY', 'D', 'EUR_JPY 03MAR2016D', '2016-03-02 22:00:00', 'long', 122.173, 121.901,
                           127.667, 121.901, 22.86),
                          ('EUR_JPY', 'D', 'EUR_JPY 27OCT2009D', '2009-10-26 22:00:00', 'short', 138.518, 138.66, 134.1,
                           136.852, 78.92),
                          ('EUR_JPY', 'D', 'EUR_JPY 15JUL2009D', '2009-07-14 22:00:00', 'long', 127.766, 126.421,
                           137.232, 130.865, 29.5),
                          ('NZD_USD', 'H12', 'NZD_USD 01JUL2019H12', '2019-07-01 09:00:00', 'short', 0.67095, 0.67258,
                           0.66328, 0.66887, 74.14),
                          ('EUR_AUD', 'D', 'EUR_AUD 04DEC2018D', '2018-12-03 22:00:00', 'long', 1.54123, 1.53398,
                           1.55752, 1.54334, 24.9),
                          ('EUR_AUD', 'D', 'EUR_AUD 08MAY2017D', '2017-05-08 22:00:00', 'short', 1.48820, 1.49191,
                           1.46223, 1.48004, 75.68),
                          ('EUR_AUD', 'D', 'EUR_AUD 24MAY2019D', '2019-05-23 22:00:00', 'short', 1.62344, 1.62682,
                           1.60294, 1.61739, 73.48),
                          ('GBP_USD', 'D', 'GBP_USD 18APR2018D', '2018-04-17 22:00:00', 'short', 1.43690, 1.43778,
                           1.41005, 1.42681, 69.42)
                          ])
def test_max_min_rsi(pair, timeframe, id, start, type, SR, SL, TP, entry, avalue):
    t = Trade(
        id=id,
        start=start,
        pair=pair,
        timeframe=timeframe,
        type=type,
        SR=SR,
        SL=SL,
        TP=TP,
        entry=entry,
        strat='counter_b1',
        settingf="../../data/settings.ini"
    )

    c = Counter(
        trade=t,
        settingf='../../data/settings.ini'
    )

    assert avalue == c.max_min_rsi()

def test_set_total_score(ct_object, clean_tmp):
    """
    Test 'set_total_score' function to set the 'total_score' class attr
    """
    ct_object.set_pivots()
    ct_object.set_total_score()
    assert ct_object.total_score == 365

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
                           [datetime.datetime(2015, 8, 23, 21, 0), datetime.datetime(2018, 12, 30, 22, 0),
                            datetime.datetime(2019, 5, 21, 21, 0)]),
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
        settingf="../../data/settings.ini"
    )

    c = Counter(
        trade=t,
        period=1000,
        settingf='../../data/settings.ini'
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

