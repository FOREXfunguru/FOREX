from pivotlist  import PivotList
from oanda_api import OandaAPI
from candlelist import CandleList

import pytest
import pdb

@pytest.fixture
def cl_object():
    '''Returns CandleList object'''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='AUD_USD',
                     granularity='D',
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22)

    oanda.run(start='2017-12-08T22:00:00',
              end='2018-01-29T22:00:00',
              roll=True)

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list, instrument='AUD_USD', type='long')

    return cl

def test_get_pivotlist(cl_object):
    '''Obtain a pivotlist'''

    pl=cl_object.get_pivotlist(outfile='test.png',th_up=0.01, th_down=-0.01)

    assert pl.slist[0].type==-1
    assert len(pl.plist)==35

def test_get_major_segment(cl_object):
    '''Test get_major_segment method'''

    pl = cl_object.get_pivotlist()

    pl.get_major_segment()

    assert pl.slist[0].count==35

