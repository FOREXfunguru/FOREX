import pytest
import pdb

from oanda_api import OandaAPI
from harea import HArea
from candlelist import CandleList
import datetime

@pytest.fixture
def oanda_object():
    '''Returns an  oanda object'''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='EUR_AUD',
                     granularity='D',
                     dailyAlignment=22,
                     alignmentTimezone='Europe/London')

    oanda.run(start='2015-08-26T22:00:00',
              end='2016-08-15T22:00:00')

    return oanda


def test_last_time(oanda_object):
    '''
    Test last_time function from HArea
    '''

    candle_list = oanda_object.fetch_candleset()

    cl = CandleList(candle_list, instrument='EUR_AUD', granularity='D')

    resist = HArea(price=0.92216, pips=50, instrument='EUR_AUD', granularity='D')

    lt=resist.last_time(clist=cl.clist, position='above')

    assert lt == datetime.datetime(2016, 8, 15, 21, 0)

def test_get_bounce_feats(oanda_object):


    candle_list = oanda_object.fetch_candleset()

    cl = CandleList(candle_list, instrument='EUR_AUD', granularity='D')

    (model, outfile) = cl.fit_reg_line()

    direction = None
    if model.coef_[0, 0] > 0:
        direction = 'up'
    else:
        direction = 'down'

    resist = HArea(price=0.92216, pips=50, instrument='EUR_AUD', granularity='D')

    (inn_bounce, bounce_pips)=resist.get_bounce_feats(clist=cl, direction=direction)

    assert inn_bounce == 5
    assert bounce_pips == 139
"""
def test_get_cross_time():

    resist = HArea(price=94.431, pips=20, instrument='CAD_JPY', granularity='H12')

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='CAD_JPY',
                     granularity='H12',
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22,
                     start='2015-01-25T22:00:00',
                     count=1)

    cross_time = resist.get_cross_time(candle=oanda.fetch_candleset()[0])

"""