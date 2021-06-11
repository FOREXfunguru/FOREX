import pytest
import logging

from harea import HArea
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

@pytest.mark.parametrize("clist_ix, price, dt", [(-1, 0.69718, 'n.a.'),
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

@pytest.mark.parametrize("clist_ix, price, dt", [(-1, 0.69718, 'n.a.'),
                                                 (-2, 0.70023, 'n.a.'),
                                                 (-3, 0.70513, 'n.a.')])
def test_get_cross_time_gran(clO, clist_ix, price, dt):
    log = logging.getLogger('Test for get_cross_time_gran')
    log.debug('cross_time_gran')

    resist = HArea(price=price,
                   pips=5,
                   instrument='AUD_USD',
                   granularity='D')

    cross_time = resist.get_cross_time(candle=clO.data['candles'][clist_ix],
                                       granularity='H1')

    assert cross_time == dt