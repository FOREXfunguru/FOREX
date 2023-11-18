import pytest

from trading_journal.open_trade import UnawareTrade

trade_details = {"start": "2020-02-19T21:00:00",
                 "pair": "EUR_GBP",
                 "type": "long",
                 "timeframe": "D",
                 "entry": 0.83585,
                 "SL": 0.82467,
                 "RR": 0.86032}


@pytest.fixture
def unaware_object(clO_pickled):
    trade_details["clist"] = clO_pickled
    return UnawareTrade(**trade_details)


def test_instantiation(unaware_object):
    assert isinstance(unaware_object, UnawareTrade)


def test_run(unaware_object):
    """Test 'run' function"""
    unaware_object.run(connect=False)