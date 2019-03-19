import pytest
import pdb

from OandaAPI import OandaAPI
from HArea import HArea

@pytest.fixture
def oanda_object():
    '''Returns an  oanda object'''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='GBP_USD',
                     granularity='D',
                     alignmentTimezone='Europe/London',
                     start='2014-01-01T22:00:00',
                     end='2019-03-15T22:00:00')

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

    resist=HArea(price=1.71690,pips=100, instrument='GBP_USD', granularity='D')

    (bounces,outfile)=resist.number_bounces(datetimes=datetimes,
                                            prices=close_prices)

