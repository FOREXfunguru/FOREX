import pytest
import pdb
import glob
import os

from apis.oanda_api import OandaAPI

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('../../data/*.data')
    for f in files:
        os.remove(f)

@pytest.mark.parametrize("i,g,s,e,resp", [('GBP_NZD', 'D', '2018-11-23T22:00:00', '2019-01-02T22:00:00', 200),
                                          ('GBP_AUD', 'D', '2002-11-23T22:00:00', '2007-01-02T22:00:00', 200),
                                          ('EUR_NZD', 'D', '2002-11-23T22:00:00', '2007-01-02T22:00:00', 200),
                                          ('AUD_USD', 'D', '2015-01-25T22:00:00', '2015-01-26T22:00:00', 200),
                                          ('AUD_USD', 'D', '2018-11-16T22:00:00', '2018-11-20T22:00:00', 200),
                                          ('AUD_USD', 'H12', '2018-11-12T10:00:00', '2018-11-14T10:00:00', 200),
                                          # End date falling in the daylight savings discrepancy(US/EU) period
                                          ('AUD_USD', 'D', '2018-03-26T22:00:00', '2018-03-29T22:00:00', 200),
                                          # End date falling in Saturday at 21h
                                          ('AUD_USD', 'D', '2018-05-21T21:00:00', '2018-05-26T21:00:00', 200),
                                          # Start and End data fall on closed market
                                          ('AUD_USD', 'D', '2018-04-27T21:00:00', '2018-04-28T21:00:00', 200),
                                          # Start date before the start of historical record
                                          ('AUD_USD', 'H12', '2000-11-21T22:00:00', '2002-06-15T22:00:00', 200)])
def test_OandaAPI(i, g, s, e, resp):
    '''
    Test a simple query to Oanda's REST API using a start and end datetimes
    '''

    oanda = OandaAPI(instrument=i,
                     granularity=g,
                     settingf='../../data/settings.ini')
    respl = oanda.run(start=s,
                      end=e)

    assert respl == resp

def test_OandaAPI_e():
    '''
    Test a simple query to Oanda's REST API using a non-valid pair
    '''

    oanda = OandaAPI(instrument='AUD_MOCK',
                     granularity='H12',
                     settingf='../../data/settings.ini')

    respl = oanda.run(start='2018-11-12T10:00:00',
                      end='2018-11-14T11:00:00')

    assert respl == 400

def test_OandaAPI_count():
    '''
    Test a simple query to Oanda's REST API using a D timeframe and using
    the 'count' parameter instead of 'end'
    '''

    oanda = OandaAPI(instrument='AUD_USD',
                     granularity='D',
                     settingf='../../data/settings.ini')

    oanda.run(start='2018-05-21T22:00:00',
              count=1)
    assert 1

def test_OandaAPI_vol():
    '''
    Test a simple query to Oanda's REST API using a H12 timeframe and using
    a volume cutoff for 'fetch_candleset' function
    '''

    oanda = OandaAPI(instrument='NZD_JPY',
                     granularity='H12',
                     settingf='../../data/settings.ini')

    oanda.run(start='2011-09-02T21:00:00',
              end='2011-09-06T22:00:00')

    candle_list = oanda.fetch_candleset(vol_cutoff=20)

    assert len(candle_list) == 6

def test_fetch_one_candle():
    oanda = OandaAPI(instrument='AUD_USD',
                     granularity='D',
                     settingf='../../data/settings.ini')

    oanda.run(start='2015-01-25T22:00:00',
              count=1)

    candle_list = oanda.fetch_candleset()
    assert candle_list[0].highBid == 0.79329
    assert candle_list[0].openBid == 0.7873
    assert candle_list[0].lowBid == 0.7857
    assert candle_list[0].representation == 'bidask'
    assert candle_list[0].lowAsk == 0.786
    assert candle_list[0].complete == True
    assert candle_list[0].openAsk == 0.7889

def test_serialize_data():
    '''
    test of function 'serialize_data'
    '''
    oanda = OandaAPI(instrument='AUD_USD',
                     granularity='D',
                     settingf='../../data/settings.ini')

    oanda.run(start='2015-01-25T22:00:00',
              count=10)

    oanda.serialize_data(outfile="../../data/out.data")

def test_run_with_seralized_data(clean_tmp):
    '''
    test oanda.run with serialized data
    '''
    oanda = OandaAPI(instrument='AUD_USD',
                     granularity='D',
                     settingf='../../data/settings_serialised.ini')

    oanda.run(start='2015-01-25T22:00:00',
              count=10)