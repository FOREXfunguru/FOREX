import pytest
import logging
import datetime

from forex.harea import HArea


@pytest.mark.parametrize(
    "clist_ix, price, dt",
    [
        (-5, 0.7267, datetime.datetime(2020, 11, 15, 22, 0)),
        (-10, 0.7002, "n.a."),
        (-30, 0.7204, datetime.datetime(2020, 10, 12, 13, 0)),
    ],
)
def test_get_cross_time(clO_pickled, clist_ix, price, dt):
    log = logging.getLogger('Test for get_cross_time')
    log.debug('cross_time')

    resist = HArea(price=price,
                   pips=5,
                   instrument='AUD_USD',
                   granularity='D')

    cross_time = resist.get_cross_time(candle=clO_pickled.candles[clist_ix],
                                       granularity='H8')

    assert cross_time == dt
