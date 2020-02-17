import pytest
import pdb

from oanda_api import OandaAPI

@pytest.fixture
def oanda_object():
    '''Returns an  oanda object'''
 
    oanda=OandaAPI(instrument='AUD_USD',
                   granularity='D',
                   settingf='data/settings.ini')

    return oanda

def test_OandaAPI1(oanda_object):
    '''
    Test a simple query to Oanda's REST API using a start and end datetimes
    '''

    oanda_object.run(start='2015-01-25T22:00:00',
                      end='2015-01-26T22:00:00')

    assert 1

def test_OandaAPI2(oanda_object):
    '''
    Test a simple query to Oanda's REST API using range of datetime where start time
    falls on Friday at 22:00:00 (when market has just closed) and code raises an Exception
    '''
    with pytest.raises(Exception):
        oanda_object.run(start='2018-11-16T22:00:00',
                         end='2018-11-20T22:00:00')
def test_OandaAPI3():
    '''
    Test a simple query to Oanda's REST API using a H12 timeframe
    '''
    oanda = OandaAPI(instrument='AUD_USD',
                   granularity='H12')

    oanda.run(start='2018-11-12T10:00:00',
              end='2018-11-14T10:00:00')

    assert 1

def test_OandaAPI4():
    '''
    Test a simple query to Oanda's REST API using a H12 timeframe and a
    non conventional time that will raise an Exception
    '''
    with pytest.raises(Exception):
        oanda=OandaAPI(instrument='AUD_USD',
                       granularity='H12',
                       alignmentTimezone='Europe/London',
                       dailyAlignment=22)

        oanda.run(start='2018-11-12T10:00:00',
                  end='2018-11-14T11:00:00')

def test_OandaAPI5():
    '''
    Test a simple query to Oanda's REST API using a H8 timeframe and a
    non conventional time that will raise an Exception
    '''
    with pytest.raises(Exception):
        oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                       instrument='AUD_USD',
                       granularity='H8',
                       alignmentTimezone='Europe/London',
                       dailyAlignment=22)

        oanda.run(start='2018-11-12T10:00:00',
                  end='2018-11-14T11:00:00')

def test_OandaAPI6():
    '''
    Test a simple query to Oanda's REST API using a H12 timeframe and a
    end date falling in the daylight savings discrepancy(US/EU) period
    '''

    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument='AUD_USD',
                   granularity='D',
                   alignmentTimezone='Europe/London',
                   dailyAlignment=22)

    oanda.run(start='2018-03-26T22:00:00',
              end='2018-03-29T22:00:00')
    assert 1

def test_OandaAPI7():
    '''
    Test a simple query to Oanda's REST API using a D timeframe and a
    end date falling in Saturday at 22h
    '''

    with pytest.raises(Exception):
        oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                       instrument='AUD_USD',
                       granularity='D',
                       alignmentTimezone='Europe/London',
                       dailyAlignment=22)

        oanda.run(start='2018-05-21T21:00:00',
                  end='2018-05-26T21:00:00')
    assert 1


def test_OandaAPI8():
    '''
    Test a simple query to Oanda's REST API using a D timeframe and using
    the 'count' parameter instead of 'end'
    '''

    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument='AUD_USD',
                   granularity='D',
                   alignmentTimezone='Europe/London',
                   dailyAlignment=22)
    oanda.run(start='2018-05-21T22:00:00',
              count=1)
    assert 1

def test_OandaAPI9():
    '''
    Test a simple query to Oanda's REST API using a D timeframe and using
    a start and end date falling on closed market
    '''

    with pytest.raises(Exception):
        oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                       instrument='AUD_USD',
                       granularity='D',
                       alignmentTimezone='Europe/London',
                       dailyAlignment=22)

        oanda.run(start='2018-04-27T21:00:00',
                  end='2018-04-28T21:00:00')

def test_OandaAPI10():
    '''
    Test a simple query to Oanda's REST API using a H12 timeframe and using
    an end date falling on closed market and the roll option=True
    '''

    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument='AUD_USD',
                   granularity='H12',
                   alignmentTimezone='Europe/London',
                   dailyAlignment=22)

    oanda.run(start='2018-04-23T21:00:00',
              end='2018-04-28T21:00:00',
              roll=True)
    
    assert 1

def test_OandaAPI11():
    '''
    Test a simple query to Oanda's REST API using a H12 timeframe and using
    an end date (with 22h) falling on closed market and the roll option=True
    '''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='AUD_USD',
                     granularity='H12',
                     roll=True,
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22)

    oanda.run(start='2018-11-21T22:00:00',
              end='2018-11-24T22:00:00',
              roll=True)

    assert 1
    

def test_OandaAPI11():
    '''
    Test a simple query to Oanda's REST API using a H12 timeframe and using
    a start date before the start of historical record
    '''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='AUD_USD',
                     granularity='H12',
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22)

    oanda.run(start='2000-11-21T22:00:00',
              end='2002-06-15T22:00:00',
              roll=True)

    assert 1

def test_OandaAPI12():
    '''
    Test a simple query to Oanda's REST API using a H12 timeframe and using
    a volume cutoff for 'fetch_candleset' function
    '''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='NZD_JPY',
                     granularity='H12',
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22)

    oanda.run(start='2011-09-02T21:00:00',
              end='2011-09-06T22:00:00',
              roll=True)

    candle_list = oanda.fetch_candleset(vol_cutoff=20)

    assert 1

def test_OandaAPI13():
    '''

    :return:
    '''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='AUD_USD',
                     granularity='H6',
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22)

    oanda.run(start='2007-05-29T16:00:00',
              end='2014-04-01T15:00:00',
              roll=True)

def test_fetch_candleset(oanda_object):
    '''
    Test how a Candle list is retrieved
    after a simple query to Oanda's REST API

    '''

    oanda_object.run(start='2018-11-04T22:00:00',
                    end='2018-11-08T22:00:00',
                    roll=True)

    candle_list = oanda_object.fetch_candleset()
    assert candle_list[0].highBid == 0.7217
    assert candle_list[0].openBid == 0.71896
    assert candle_list[0].lowBid == 0.71821
    assert candle_list[0].representation == 'bidask'
    assert candle_list[0].lowAsk == 0.71835
    assert candle_list[0].complete == True
    assert candle_list[0].openAsk == 0.71958
    assert candle_list[0].highAsk == 0.72187
    assert candle_list[0].highBid == 0.7217
    assert candle_list[0].volume == 8476
    assert candle_list[0].closeBid == 0.72084
    assert candle_list[0].closeAsk == 0.72118
    assert candle_list[0].openBid == 0.71896

def test_fetch_one_candle():
    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='AUD_USD',
                     granularity='D',
                     dailyAlignment=22,
                     alignmentTimezone='Europe/London',
                     start='2015-01-25T22:00:00',
                     count=1)

    oanda.run(start='2015-01-25T22:00:00',
              count=1)

    candle_list=oanda.fetch_candleset()
    assert candle_list[0].highBid == 0.79329
    assert candle_list[0].openBid == 0.7873
    assert candle_list[0].lowBid == 0.7857
    assert candle_list[0].representation == 'bidask'
    assert candle_list[0].lowAsk == 0.786
    assert candle_list[0].complete == True
    assert candle_list[0].openAsk == 0.7889
"""