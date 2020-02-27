from Pattern.counter import Counter

import pytest
import pdb
import datetime
import glob
import os
from TradeJournal.trade import Trade

@pytest.fixture
def ct_object():
    '''Returns Counter object'''

    t = Trade(
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
        id='EUR_GBP 13AUG2019D',
        trade=t,
        period=1000,
        trend_i='2019-05-03 21:00:00',
        settingf='data/settings.ini'
    )
    return c

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('data/tmp/*')
    for f in files:
        os.remove(f)

def test_clist_period(ct_object):
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
                         "lasttime", [('2018-12-03 22:00:00','long',1.54123,1.53398,1.55752,1.54334,datetime.datetime(2018, 6, 5, 21, 0)),
                                      ('2018-09-11 22:00:00','short',1.63118,1.63633,1.60202,1.62763,datetime.datetime(2009, 11, 29, 22, 0)),
                                      ('2017-05-05 22:00:00','short',1.48820,1.49191,1.46223,1.48004,datetime.datetime(2016, 9, 15, 21, 0)),
                                      ('2019-05-23 22:00:00','short',1.62344,1.62682,1.60294,1.61739,datetime.datetime(2018, 10, 4, 21, 0))])
def test_lasttime_attr(start, type, SR, SL, TP, entry, lasttime):
    """
    Check that self.lasttime class attribute
    has been initialized
    """
    t = Trade(
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
        id='test',
        trade=t,
        period=1000,
        settingf='data/settings.ini'
    )
    c.set_lasttime()
    assert c.lasttime == lasttime

def test_bounces_attr(counter_object):
    """
    Check that self.bounces class attribute
    has been initialized
    """

    assert counter_object.bounces.plist[0].candle.midAsk==0.9398
    assert len(counter_object.bounces.plist)==3

def test_bounces_lasttime_attr(counter_object):
    """
    Check that self.bounces_lasttime class attribute
    has been initialized
    """

    assert len(counter_object.bounces_lasttime.plist)==3

def test_calc_score(counter_object):
    """
    Test 'calc_score' function to set the 'total_score' class attr
    """

    assert counter_object.total_score==511

def test_calc_score_lasttime(counter_object):
    '''Test 'calc_score_lasttime' function to set the 'score_lasttime' class attr'''

    assert counter_object.score_lasttime==511

"""
def test_calc_itrend(counter_object_notrendi):

    counter_object_notrendi.calc_itrend()


def test_bounces_fromlasttime(counter_object):

    counter_object.set_bounces()
    counter_object.set_lasttime()
    counter_object.bounces_fromlasttime()

    assert counter_object.bounces[0][0].strftime('%Y-%m-%d') == '2018-10-10'
    assert counter_object.bounces[0][1] == 1.87111

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