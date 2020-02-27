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

@pytest.mark.parametrize("start,type,SR,SL,TP, lasttime", [('AUD_USD', 'D', '2015-01-25T22:00:00', '2015-01-26T22:00:00', 200),
                                          ('AUD_USD', 'D', '2018-11-16T22:00:00', '2018-11-20T22:00:00', 200)])
def test_lasttime_attr(counter_object):
    """
    Check that self.lasttime class attribute
    has been initialized
    """
    t = Trade(
        start=start,
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


    adatetime = datetime.datetime(2009, 3, 22, 21, 0)
    assert counter_object.lasttime==adatetime

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