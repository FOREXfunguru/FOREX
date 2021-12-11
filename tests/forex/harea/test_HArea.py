import pytest
import logging
import pdb

from forex.harea import HArea

@pytest.mark.parametrize("clist_ix, price, dt", [(-1, 0.72670, 'n.a.'),
                                                 (-2, 0.70023, 'n.a.'),
                                                 (-3, 0.70513, 'n.a.')])
def test_get_cross_time(clO_pickled, clist_ix, price, dt):
    log = logging.getLogger('Test for get_cross_time')
    log.debug('cross_time')

    resist = HArea(price=price,
                   pips=5,
                   instrument='AUD_USD',
                   granularity='D')

    cross_time = resist.get_cross_time(candle=clO_pickled[clist_ix])

    assert cross_time == dt