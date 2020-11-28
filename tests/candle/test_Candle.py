'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
import pytest

from candle.candle import BidAskCandle

@pytest.fixture
def BidAskCandle_o():
    '''
    BidAskCandle object instantiation
    '''

    candle = BidAskCandle(openAsk=0.7889,
                          openBid=0.7889,
                          granularity='D',
                          instrument='AUD_USD',
                          closeAsk=0.79258,
                          closeBid=0.79258,
                          highAsk=0.79347,
                          highBid=0.79347,
                          lowAsk=0.786,
                          lowBid=0.786,
                          complete=True,
                          volume=12619,
                          representation='bidask',
                          time='2015-01-25 22:00:00')

    return candle

def test_set_candle_features(BidAskCandle_o):
    '''
    Test function to set basic candle features based on price
    i.e. self.colour, upper_wick, etc...
    '''

    BidAskCandle_o.set_candle_features()
    assert candle_list[0].colour == colour
    assert candle_list[0].upper_wick == upper_wick
    assert candle_list[0].lower_wick == lower_wick

@pytest.mark.parametrize("pair,"
                         "timeframe,"
                         "time,"
                         "is_it",
                         [('AUD_USD', 'D', '2020-03-18T22:00:00', True),
                          ('AUD_USD', 'D', '2019-07-31T22:00:00', False),
                          ('AUD_USD', 'D', '2019-03-19T22:00:00', False),
                          ('AUD_USD', 'D', '2020-01-22T22:00:00', True)])
def test_indecision_c(pair, timeframe, time, is_it):
    oanda = OandaAPI(instrument=pair,
                     granularity=timeframe,
                     settingf="../../data/settings.ini")

    oanda.run(start=time,
              count=1)

    candle_list = oanda.fetch_candleset()
    candle_list[0].set_candle_features()
    result = candle_list[0].indecision_c()

    assert is_it == result
