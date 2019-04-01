from Pattern.CounterDbTp import CounterDbTp

import pytest

@pytest.fixture
def ctdbptp_object():
    '''Returns CounterDbTp object'''

    ctdbptp = CounterDbTp(
                        start='2019-02-21T22:00:00',
                        pair='GBP_AUD',
                        timeframe='H12')

    return ctdbptp