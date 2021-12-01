import pytest
import logging
import pdb

from forex.harea import HArea
import datetime

def test_last_time(clO):
    log = logging.getLogger('Test for last_time function')
    log.debug('last_time')

    resist = HArea(price=0.70151,
                   pips=5,
                   instrument='AUD_USD',
                   granularity='D')

    lt = resist.last_time(clist=clO.data['candles'], position='above')

    assert lt == datetime.datetime(2019, 7, 21, 21, 0)

@pytest.mark.parametrize("clist_ix, price, dt", [(-1, 0.68180, '2020-01-24T03:00:00.000000000Z'),
                                                 (-2, 0.70023, 'n.a.'),
                                                 (-3, 0.70513, 'n.a.')])
def test_get_cross_time(clO, clist_ix, price, dt):
    log = logging.getLogger('Test for get_cross_time')
    log.debug('cross_time')

    resist = HArea(price=price,
                   pips=5,
                   instrument='AUD_USD',
                   granularity='D')

    cross_time = resist.get_cross_time(candle=clO.data['candles'][clist_ix])

    assert cross_time == dt