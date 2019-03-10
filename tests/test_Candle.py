import pytest

from OandaAPI import OandaAPI

@pytest.fixture
def oanda_object():
    '''Returns an  oanda object'''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='AUD_USD',
                     granularity='D',
                     alignmentTimezone='Europe/London',
                     start='2015-01-25T22:00:00',
                     end='2015-01-26T22:00:00')
    return oanda

def test_set_candle_features(oanda_object):
    '''
    Test function to set basic candle features based on price
    i.e. self.colour, upper_wick, etc...
    '''

    candle_list = oanda_object.fetch_candleset()
    candle_list[0].set_candle_features()

    assert candle_list[0].colour == "green"
