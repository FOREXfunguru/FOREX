import pytest
import pdb

from trading_journal.open_trade import UnawareTrade

trade_details = {"start": "2021-02-19T21:00:00",
                 "pair": "AUD_USD",
                 "type": "long",
                 "timeframe": "H8",
                 "entry": 0.83585,
                 "SL": 0.82467,
                 "RR": 0.86032}


@pytest.fixture
def unaware_object(clO_H8_pickled, clO_D_2021pickled):
    trade_details["clist"] = clO_H8_pickled
    return UnawareTrade(clist_tm=clO_D_2021pickled,
                        **trade_details)


def test_instantiation(unaware_object):
    assert isinstance(unaware_object, UnawareTrade)


def test_run(unaware_object):
    """Test 'run' function"""
    unaware_object.run(connect=False)
