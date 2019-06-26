from Pattern.counter import Counter

import pytest
import pdb

@pytest.fixture
def counter_object():
    '''Returns Counter object'''

    c = Counter(
                start='2018-10-11 21:00:00',
                pair='GBP_AUD',
                timeframe='H12',
                type='short',
                period=1000,
                SR=1.87074,
                SL=1.87384,
                TP=1.83942,
                trend_i='2018-08-08 21:00:00')
    return c

@pytest.fixture
def counter_object_notrendi():
    '''Returns Counter object without the 'trend_i' initialised'''

    c = Counter(
                start='2018-10-11 21:00:00',
                pair='GBP_AUD',
                timeframe='H12',
                type='short',
                period=1000,
                entry=1.85929,
                SR=1.87074,
                SL=1.87384,
                RR=1.5)
    return c
"""
def test_calc_itrend(counter_object_notrendi):

    counter_object_notrendi.calc_itrend()


def test_get_bounces(counter_object):

    counter_object.set_bounces()

    assert counter_object.bounces[0][0].strftime('%Y-%m-%d') == '2018-10-10'
    assert counter_object.bounces[0][1] == 1.87111

def test_last_time(counter_object):

    assert counter_object.set_lasttime()==None

def test_bounces_fromlasttime(counter_object):

    counter_object.set_bounces()
    counter_object.set_lasttime()
    counter_object.bounces_fromlasttime()

    assert counter_object.bounces[0][0].strftime('%Y-%m-%d') == '2018-10-10'
    assert counter_object.bounces[0][1] == 1.87111
"""
def test_set_slope(counter_object):

    counter_object.set_slope()

    assert counter_object.slope==0.0011973711767399185
"""
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