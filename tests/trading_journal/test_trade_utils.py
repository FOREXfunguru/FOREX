import pytest
import pdb
import datetime

from trading_journal.trade_utils import *
from trading_journal.trade import Trade
from api.oanda.connect import Connect
from forex.candle import CandleList

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

def test_calc_trade_session(t_object):

    t_object.run_trade()
    assert calc_trade_session(t_object) == 'nosession'

@pytest.mark.parametrize("start,"
                         "end,"
                         "type",
                         [(datetime(2018, 4, 27, 22, 0, 0), datetime(2020, 4, 27, 21, 0, 0), 'long'),
                          (datetime(2018, 3, 18, 21, 0, 0), datetime(2020, 3, 18, 21, 0, 0), 'short'),
                          (datetime(2018, 2, 17, 21, 0, 0), datetime(2020, 2, 17, 21, 0, 0), 'long'),
                          (datetime(2017, 8, 11, 21, 0, 0), datetime(2019, 8, 11, 21, 0, 0), 'short'),
                          (datetime(2017, 1, 9, 21, 0, 0), datetime(2019, 1, 9, 21, 0, 0), 'short')])
def test_get_trade_type(start, end, type):
    conn = Connect(instrument='EUR_GBP',
                   granularity='D')

    cl = conn.query(start=start.isoformat(),
                     end=end.isoformat())

    assert type == get_trade_type(end, cl)

def test_calc_adr(t_object):
    t_object.period = t_object.initclist()
    calc_adr(t_object)
    assert 0
