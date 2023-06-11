import pytest
import logging

from forex.candle import CandleList

@pytest.fixture
def clO():
    log = logging.getLogger('cl_object')
    log.debug('Create a CandleList object')

    alist = [
        {
         'time': '2018-11-18T22:00:00',
         'o': '0.73093',
         'h': '0.73258',
         'l': '0.72776',
         'c': '0.72950'},
        {
         'time': '2018-11-19T22:00:00',
         'o': '0.70123',
         'h': '0.75123',
         'l': '0.68123',
         'c': '0.72000'
         }
    ]
    cl = CandleList(instrument='AUD_USD',
                    granularity='D',
                    data=alist)
    return cl


@pytest.fixture
def clO1():
    log = logging.getLogger('cl_object')
    log.debug('Create a CandleList object')

    alist = [
        {
         'time': '2018-11-20T22:00:00',
         'o': '0.73093',
         'h': '0.73258',
         'l': '0.72776', 
         'c': '0.72950'},
        {
         'time': '2018-11-21T22:00:00',
         'o': '0.70123',
         'h': '0.75123',
         'l': '0.68123', 
         'c': '0.72000'
         }
    ]
    cl = CandleList(instrument='AUD_USD',
                    granularity='D',
                    data=alist)
    return cl
