import pytest
import pdb

from trading_journal.trade import UnawareTrade

@pytest.fixture
def trade_dict(clOH8_2019_pickled, clO_pickled):
    trade_details = {"pair": "AUD_USD",
                     "type": "long",
                     "timeframe": "H8",
                     "clist": clOH8_2019_pickled,
                     "clist_tm": clO_pickled}
    return trade_details

def test_instantiation(trade_dict):
    trade_dict["entry"] = 0.68900
    trade_dict["SL"] = 0.67288
    trade_dict["TP"] = 0.71348
    trade_dict["start"] = "2019-06-18T21:00:00"
    assert isinstance(UnawareTrade(**trade_dict), UnawareTrade)

trade_data = [(0.89, 0.95, 0.93, "2019-06-18T21:00:00"),
              (0.89, 0.95, 0.93, "2019-06-18T21:00:00"),
              (0.89, 0.95, 0.93, "2019-06-18T21:00:00")]

outcomes = []

@pytest.mark.parametrize("entry, SL, TP, start", trade_data)
def test_run_trade(trade_dict, entry, SL, TP, start):
    """Test 'run_trade' function"""
    pdb.set_trace()
    trade_dict["entry"] = entry
    trade_dict["SL"] = SL
    trade_dict["TP"] = TP
    trade_dict["start"] = start
    unaware_object = UnawareTrade(**trade_dict)
    unaware_object.run_trade(connect=False)
    pdb.set_trace()
    print("h")

