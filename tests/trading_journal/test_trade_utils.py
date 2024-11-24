import pytest

from forex.candle import Candle
from trading_journal.trade_utils import (
    get_closest_hour,
    process_start,
    adjust_SL,
    check_timeframes_fractions)
from data_for_tests import start_hours

hour_data = [(9, "H8", 5), (21, "H8", 21), (17, "H8", 13)]


@pytest.mark.parametrize("solve_hour,timeframe,closest_hour", hour_data)
def test_get_closest_hour(solve_hour, timeframe, closest_hour):
    """Test the 'get_closest_hour' function"""
    assert get_closest_hour(timeframe=timeframe, solve_hour=solve_hour) == closest_hour


@pytest.mark.parametrize("start,returned,timeframe", start_hours)
def test_process_start(start, returned, timeframe):
    aligned_start = process_start(dt=start, timeframe=timeframe)
    assert aligned_start == returned


fraction_data = [("D", "H8", 3.0), ("H12", "H8", 1.5),  ("H8", "H4", 2.0)]


@pytest.mark.parametrize("timeframe1,timeframe2,fraction", fraction_data)
def test_check_timeframes_fractions(timeframe1, timeframe2, fraction):
    res_fraction = check_timeframes_fractions(timeframe1=timeframe1,
                                              timeframe2=timeframe2)
    assert res_fraction == fraction


def test_get_SLdiff(t_object):
    assert 24.0 == t_object.get_SLdiff()


# lisf of lists containing tuples, where each tuple is composed of a candle high and low
high_low_candles = [
    [(0.80, 0.70), (0.82, 0.70), (0.79, 0.70)],
    [(0.90, 0.70), (0.95, 0.65), (0.97, 0.72)],
]
# trade types for each sublist in 'high_low_candles'
trade_types = ["short", "long"]
# adjusted SL prices
sl_adjusted = [0.821, 0.649]


@pytest.fixture
def mock_candle_list(mocker):
    """Creates a list of lists, each sublist containing 3 mocked Candle objects"""
    tri_candle_list = list()
    for tri_candle in high_low_candles:
        candle_list = list()
        for high_low in tri_candle:
            mock_Candle_instrance = mocker.MagicMock(spec=Candle)
            mocker.patch.object(mock_Candle_instrance, "h", high_low[0])
            mocker.patch.object(mock_Candle_instrance, "l", high_low[1])
            candle_list.append(mock_Candle_instrance)
        tri_candle_list.append(candle_list)
    return tri_candle_list


def test_adjust_sl(mock_candle_list):
    """Test 'adjust_sl' function"""

    for ix in range(len(mock_candle_list)):
        tri_candle = mock_candle_list[ix]
        new_SL = adjust_SL(
            pair="AUD_USD", type=trade_types[ix], list_candles=tri_candle
        )
        assert sl_adjusted[ix] == new_SL
