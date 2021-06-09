import pytest
import pdb
import datetime

from trading_journal.trade import Trade

def test_fetch_candlelist(t_object):
    '''
    This test checks the function to return a CandleList object 
    corresponding to this trade
    '''
    
    cl = t_object.fetch_candlelist()
    assert cl.data['candles'][0]['openBid'] == 0.74884
    assert cl.data['candles'][0]['highBid'] == 0.75042

@pytest.mark.parametrize("pair,start,type,SL,TP,entry, outcome", [
        ('AUD/NZD', '2020-05-18 21:00:00', 'short', 1.08369, 1.06689, 1.07744, 'success'),
        ('NZD/JPY', '2019-03-22 21:00:00', 'short', 76.797, 73.577, 75.509, 'success'),
        ('AUD/CAD', '2009-10-27 21:00:00', 'short', 0.98435, 0.9564, 0.97316, 'failure'),
        ('EUR/GBP', '2009-09-21 21:00:00', 'short', 0.90785, 0.8987, 0.90421, 'failure'),
        ('EUR/GBP', '2010-02-06 22:00:00', 'long', 0.86036, 0.8977, 0.87528, 'success'),
        ('EUR/AUD', '2018-12-03 22:00:00', 'long', 1.53398, 1.55752, 1.54334, 'success'),
        ('EUR/AUD', '2018-09-11 22:00:00', 'short', 1.63633, 1.60202, 1.62763, 'success'),
        ('EUR/AUD', '2017-05-05 22:00:00', 'short', 1.49191, 1.46223, 1.48004, 'failure'),
        ('EUR/AUD', '2019-05-23 22:00:00', 'short', 1.62682, 1.60294, 1.61739, 'failure')
])
def test_run_trade(pair, start, type, SL, TP, entry, outcome):
    '''
    This test checks the progression of the Trade
    and checks if the outcome attribute is correctly
    defined.
    '''
    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair=pair,
            type=type,
            timeframe="D",
            strat="counter_b2",
            id="test")

    td.run_trade()
    assert td.outcome == outcome

@pytest.mark.parametrize("pair,start,type,SL,TP,entry,entered", [('EUR/GBP', '2017-03-14 22:00:00', 'short', 0.87885,
                                                                  0.8487, 0.86677, True),
                                                                 ('EUR/GBP', '2016-10-05 22:00:00', 'short', 0.8848,
                                                                  0.86483, 0.87691, False),
                                                                 ('EUR/AUD', '2018-12-03 22:00:00', 'long', 1.53398,
                                                                 1.55752, 1.54334, True)])
def test_run_trade_wexpire(pair, start, type, SL, TP, entry, entered):
    '''
    This test checks the run_trade method with the 'expires' parameter
    '''
    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair=pair,
            type=type,
            timeframe="D",
            strat="counter_b2",
            id="test")

    td.run_trade(expires=2)
    assert td.entered == entered

@pytest.mark.parametrize("pair,start,type,SL,TP,entry,entered", [('EUR/GBP', '2020-04-21 17:00:00', 'long', 0.88209,
                                                                  0.89279, 0.88636, False)])
def test_run_trade_wexpire_4hrs(pair, start, type, SL, TP, entry, entered):
    '''
    This test checks the run_trade method with the 'expires' parameter
    '''
    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair=pair,
            type=type,
            timeframe="H4",
            strat="counter_b2",
            id="test")

    td.run_trade(expires=2)
    assert td.entered == entered

@pytest.mark.parametrize("pair,start,type,SL,TP,entry,outcome", [('EUR/GBP', '2019-05-06 01:00:00', 'long', 0.84881,
                                                                  0.85682, 0.85121, 'success'),
                                                                 ('EUR/GBP', '2020-03-25 13:00:00', 'long', 0.90494,
                                                                  0.93197, 0.91553, 'failure')])
def test_run_trade_4hrs(pair, start, type, SL, TP, entry, outcome):
    '''
    This test checks the run_trade method with the 'expires' parameter
    '''
    td = Trade(
            start=start,
            entry=entry,
            SL=SL,
            TP=TP,
            pair=pair,
            type=type,
            timeframe="H4",
            strat="counter_b2",
            id="test")

    td.run_trade()
    assert td.outcome == outcome

def test_get_SLdiff(t_object):

    assert 41.9 == t_object.get_SLdiff()

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
def test_get_trend_i(pair, id, timeframe, start, type, SR, SL, TP, entry, trend_i):
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
        strat='counter_b1')

    assert trend_i == t.trend_i
