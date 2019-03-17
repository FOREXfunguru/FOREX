import pytest

from OandaAPI import OandaAPI
from HArea import HArea

@pytest.fixture
def oanda_object():
    '''Returns an  oanda object'''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='AUD_USD',
                     granularity='D',
                     alignmentTimezone='Europe/London',
                     start='2015-03-12T22:00:00',
                     end='2019-03-12T22:00:00')

    return oanda

def test_number_bounces(oanda_object):
    '''
    Test function to set basic candle features based on price
    i.e. self.colour, upper_wick, etc...
    '''

    candle_list = oanda_object.fetch_candleset()

    close_prices = []
    datetimes = []
    for c in oanda_object.fetch_candleset():
        close_prices.append(c.closeAsk)
        datetimes.append(c.time)

    resist=HArea(price=0.81173,pips=10)