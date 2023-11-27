import pytest
import datetime

import numpy as np

from trading_journal.trade_utils import (is_entry_onrsi,
                                         get_lasttime,
                                         get_max_min_rsi)
from trading_journal.trade import Trade
from forex.harea import HAreaList, HArea


@pytest.fixture
def halist_factory():
    hlist = []
    for p in np.arange(0.610, 0.80, 0.020):
        area = HArea(price=p,
                     pips=30,
                     instrument="AUD_USD",
                     granularity="D")
        hlist.append(area)

    halist = HAreaList(halist=hlist)
    return halist


trades = [('EUR_GBP', 'D', 'EUR_GBP 23FEB2007D', '2007-02-22 22:00:00',
           'short', 0.6713, 0.6758, 0.6615, 0.67009),
          ('EUR_JPY', 'D', 'EUR_JPY 04MAY2016D', '2016-05-03 22:00:00',
           'long', 122.173, 121.57, 125.138, 123.021),
          ('EUR_JPY', 'D', 'EUR_JPY 06APR2010D', '2010-04-05 22:00:00',
           'short', 126.909, 128.151, 124.347, 126.627),
          ('EUR_JPY', 'D', 'EUR_JPY 27OCT2009D', '2009-10-26 22:00:00',
           'short', 138.518, 138.66, 134.1, 136.852),
          ('EUR_JPY', 'H8', 'EUR_JPY 21OCT2009H8', '2009-10-21 13:00:00',
           'short', 121.055, 123.0, 120.166, 121.517),
          ('EUR_JPY', 'H8', 'EUR_JPY 04JUN2020H8', '2020-06-04 21:00:00',
           'short', 124.058, 124.478, 121.648, 123.655)]
is_on_rsi = [False, False, False, False, True, True]

trade_data1 = [(*trade, pip) for trade, pip in zip(trades, is_on_rsi)]


@pytest.mark.parametrize("pair,timeframe,id,start,type,SR,SL,TP,"
                         "entry,entry_onrsi", trade_data1)
def test_is_entry_onrsi(pair, id, timeframe, start, type, SR, SL, TP, entry,
                        entry_onrsi):
    """Test is_entry_onrsi function"""

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
        init_clist=True)
    newclist = t.clist
    newclist.calc_rsi()
    t.clist = newclist

    assert entry_onrsi == is_entry_onrsi(t)


trades1 = [('2017-12-10 22:00:00', 'long', 0.74986, 0.74720, 
            0.76521, 0.75319),
           ('2018-09-11 22:00:00', 'short', 1.63118, 1.63633,
            1.60202, 1.62763),
           ('2017-05-05 22:00:00', 'short', 1.48820, 1.49191,
            1.46223, 1.48004),
           ('2019-05-23 22:00:00', 'short', 1.62344, 1.62682,
            1.60294, 1.61739)]

datetimes1 = [datetime.datetime(2017, 6, 4, 21, 0),
              datetime.datetime(2010, 11, 16, 22, 0),
              datetime.datetime(2010, 11, 16, 22, 0),
              datetime.datetime(2010, 11, 16, 22, 0)]

trade_data2 = [(*trade, pip) for trade, pip in zip(trades1, datetimes1)]


@pytest.mark.parametrize("start,type,SR,SL,TP,entry,lasttime", trade_data2)
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

    assert get_lasttime(t) == lasttime


@pytest.mark.parametrize("start,"
                         "type,"
                         "SR,"
                         "SL,"
                         "TP,"
                         "entry,"
                         "lasttime",
                         [('2017-12-10 22:00:00', 'long', 0.74986, 0.74720,
                          0.76521, 0.75319,
                          datetime.datetime(2017, 6, 1, 21, 0)),
                          ('2017-03-21 22:00:00', 'short', 0.77103, 0.77876,
                           0.73896, 0.76717,
                           datetime.datetime(2016, 4, 19, 21, 0))])
def test_get_lasttime_with_pad(start, type, SR, SL, TP, entry, lasttime,
                               clO_pickled):
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

    assert get_lasttime(t, pad=30) == lasttime


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
                         [('EUR_GBP', 'D', 'EUR_GBP 23FEB2007D',
                           '2007-02-22 22:00:00', 'short', 0.6713, 0.6758,
                           0.6615, 0.67009, 64.48),
                          ('EUR_GBP', 'D', 'EUR_GBP 04JUN2004D',
                          '2004-06-03 22:00:00', 'long', 0.66379, 0.66229, 
                           0.67418, 0.66704, 37.94)])
def test_max_min_rsi(pair, timeframe, id, start, type, SR, SL, TP, entry, 
                     avalue, clO_pickled):
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
        strat="counter_b1",
        clist=clO_pickled)

    assert avalue == get_max_min_rsi(t)

def test_get_SLdiff(t_object):
    assert 24.0 == t_object.get_SLdiff()

