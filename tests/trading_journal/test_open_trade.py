import pytest

from trading_journal.open_trade import UnawareTrade

trade_details = {"start": "2019-06-18T21:00:00",
                 "pair": "AUD_USD",
                 "type": "long",
                 "timeframe": "H8",
                 "entry": 0.68900,
                 "SL": 0.67288,
                 "TP": 0.71348}

@pytest.fixture
def unaware_object(clOH8_2019_pickled, clO_pickled):
    trade_details["clist"] = clOH8_2019_pickled
    return UnawareTrade(clist_tm=clO_pickled,
                        **trade_details)


def test_instantiation(unaware_object):
    assert isinstance(unaware_object, UnawareTrade)


def test_run(unaware_object):
    """Test 'run' function"""
    unaware_object.run(connect=False)
