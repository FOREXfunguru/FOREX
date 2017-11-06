import pytest
import pdb

from OandaAPI import OandaAPI
from CandleList import CandleList

@pytest.fixture
def oanda_object():
    '''Returns an  oanda object'''

    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument='AUD_USD',
                   granularity='D',
                   alignmentTimezone='Europe/London',
                   dailyAlignment=22,
                   start='2015-01-26T22:00:00',
                   end='2015-01-29T22:00:00')

    return oanda


def test_CandleList():
    '''
    Test the creation of a CandleList object

    '''
    # time must be in a valid datetime format
    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument='AUD_USD',
                   granularity='D',
                   alignmentTimezone='Europe/London',
                   start='2015-01-25T22:00:00',
                   end='2015-01-26T22:00:00')

    candle_list=oanda.fetch_candleset()

    cl=CandleList(candle_list)

    one_c=cl.next()
    assert one_c.highBid==0.79328
    assert one_c.openBid==0.7873
    assert one_c.lowBid==0.7857
    assert one_c.representation=='bidask'
    assert one_c.lowAsk==0.786
    assert one_c.complete==True
    assert one_c.openAsk==0.7889
    assert one_c.highAsk==0.79345
    assert one_c.highBid==0.79328
    assert one_c.volume==11612
    assert one_c.closeBid==0.79316
    assert one_c.closeAsk==0.79335
    assert one_c.openBid==0.7873

def test_get_binary_seq(oanda_object):
    '''
    Test the method create a sequence of 1s and 0s
    '''
    
    candle_list=oanda_object.fetch_candleset()

    cl=CandleList(candle_list)

    seq1=cl.get_binary_seq('short','high')
    seq2=cl.get_binary_seq('short','low')
    seq3=cl.get_binary_seq('short','open')
    seq4=cl.get_binary_seq('short','close')
    seq5=cl.get_binary_seq('short','colour')

    assert seq1=="01"
    assert seq2=="11"
    assert seq3=="01"
    assert seq4=="11"
    assert seq5=="011"

