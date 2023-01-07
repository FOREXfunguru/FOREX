import pytest
import pdb
import datetime

from trading_journal.trade_utils import *
from trading_journal.trade import Trade
import numpy as np

@pytest.fixture
def halist_factory():
    hlist = []
    for p in np.arange(0.610, 0.80, 0.020):
        area = HArea(price=p,
                     pips=30,
                     instrument='AUD_USD',
                     granularity='D')
        hlist.append(area)

    halist = HAreaList(halist=hlist)
    return halist

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
                           False),
                          ('EUR_JPY', 'H8', 'EUR_JPY 04JUN2020H8', '2020-06-04 21:00:00', 'short', 124.058, 124.478, 121.648,
                           123.655, False)])
def test_is_entry_onrsi(pair, id, timeframe, start, type, SR, SL, TP, entry, entry_onrsi, clO_pickled):
    '''Test is_entry_onrsi function'''

    clO_pickled.calc_rsi()
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
        init=True,
        clist=clO_pickled)

    assert entry_onrsi == is_entry_onrsi(t)

@pytest.mark.parametrize("start,"
                         "type,"
                         "SR,"
                         "SL,"
                         "TP,"
                         "entry,"
                         "lasttime",
                         [('2018-12-03 22:00:00', 'long', 1.54123, 1.53398, 1.55752, 1.54334,
                           datetime(2010, 11, 16, 22, 0)),
                          ('2018-09-11 22:00:00', 'short', 1.63118, 1.63633, 1.60202, 1.62763,
                           datetime(2010, 11, 16, 22, 0)),
                          ('2017-05-05 22:00:00', 'short', 1.48820, 1.49191, 1.46223, 1.48004,
                           datetime(2010, 11, 16, 22, 0)),
                          ('2019-05-23 22:00:00', 'short', 1.62344, 1.62682, 1.60294, 1.61739,
                           datetime(2010, 11, 16, 22, 0))])
def test_get_lasttime(start, type, SR, SL, TP, entry, lasttime, clO_pickled):
    """Check function get_lasttime"""
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
        init=True,
        clist=clO_pickled)

    assert get_lasttime(t)  == lasttime

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
                           0.67009, 64.48),
                          ('EUR_GBP', 'D', 'EUR_GBP 04JUN2004D', '2004-06-03 22:00:00', 'long', 0.66379, 0.66229, 0.67418,
                           0.66704, 37.94)])
def test_max_min_rsi(pair, timeframe, id, start, type, SR, SL, TP, entry, avalue, clO_pickled):
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
        clist=clO_pickled)

    assert avalue == get_max_min_rsi(t)

"""
TOFIX
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
                         [('AUD_USD', 'D', 'AUD_USD 09FEB2010D', '2010-02-08 22:00:00', 'long', 76.820, 76.094, 80.289, 77.764,
                           24.1),
                          ('AUD_JPY', 'D', 'AUD_JPY 16MAR2010D', '2010-03-15 21:00:00', 'short', 82.63, 83.645, 80.32, 82.315,
                           13.4)])
def test_calc_pips_c_trend(pair, id, timeframe, start, type, SR, SL, TP, entry, pips_c_trend, clO_pickled, clean_tmp):
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
        clist=clO_pickled,
        strat='counter_b1')

    assert pips_c_trend == calc_pips_c_trend(t)
"""

def test_calc_trade_session(t_object):

    t_object.run_trade()
    assert calc_trade_session(t_object) == 'nosession'

@pytest.mark.parametrize("start,"
                         "end,"
                         "type",
                         [(datetime(2018, 4, 27, 22, 0, 0), datetime(2020, 4, 27, 21, 0, 0), 'short'),
                          (datetime(2018, 5, 18, 21, 0, 0), datetime(2020, 3, 18, 21, 0, 0), 'long'),
                          (datetime(2018, 6, 17, 21, 0, 0), datetime(2020, 1, 17, 21, 0, 0), 'long'),
                          (datetime(2018, 7, 11, 21, 0, 0), datetime(2019, 8, 11, 21, 0, 0), 'long'),
                          (datetime(2018, 1, 9, 21, 0, 0), datetime(2019, 1, 9, 21, 0, 0), 'short')])
def test_get_trade_type(start, end, type, clO_pickled):
    new_cl = clO_pickled.slice(start=start,
                               end=end)

    assert type == get_trade_type(end, new_cl)

def test_adjust_SL_candles_short(clO_pickled):
    """Test adjust_SL_candles function with a short trade"""
    start = datetime(2018, 9, 2, 21, 0)
    end = datetime(2020, 9, 2, 21, 0)
    subClO = clO_pickled.slice(start=start, end=end)
    SL = adjust_SL_candles('short', subClO)

    assert SL==0.74138

def test_adjust_SL_candles_long(clO_pickled):
    """Test adjust_SL_candles function with a short trade"""
    start = datetime(2019, 9, 28, 21, 0)
    end = datetime(2020, 9, 28, 21, 0)
    subClO = clO_pickled.slice(start=start, end=end)
    SL = adjust_SL_candles('long', subClO)

    assert SL==0.70061

def test_adjust_SL_pips_short():
    SL = adjust_SL_pips(0.75138, 'short', pair='AUD_USD')
    assert 0.7614 == SL

def test_adjust_SL_pips_long():
    SL = adjust_SL_pips(0.75138, 'long', pair='AUD_USD')
    assert 0.7414 == SL

def test_adjust_SL_nextSR(halist_factory):
    SL, TP = adjust_SL_nextSR(halist_factory, 2, 'short')
    assert SL == 0.67
    assert TP == 0.63

"""
TOFIX
def test_calc_adr(t_object):
    t_object.period = t_object.initclist()
    calc_adr(t_object)
    assert 0
"""
