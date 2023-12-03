import datetime
import pytest
import numpy as np

from forex.harea import HAreaList, HArea
from trade_bot.trade_bot_utils import (adjust_SL_pips, 
                                       get_trade_type,
                                       adjust_SL_candles,
                                       adjust_SL_nextSR)

@pytest.fixture
def halist_factory():
    hlist = []
    for p in np.arange(0.610, 0.80, 0.020):
        area = HArea(price=p, pips=30, instrument="AUD_USD", granularity="D")
        hlist.append(area)

    halist = HAreaList(halist=hlist)
    return halist

def test_adjust_SL_pips_short(clO_pickled):
    clObj = clO_pickled.candles[10]
    SL = adjust_SL_pips(clObj, "short", pair="AUD_USD")
    assert 0.9814 == SL


def test_adjust_SL_pips_long(clO_pickled):
    clObj = clO_pickled.candles[100]
    SL = adjust_SL_pips(clObj, "long", pair="AUD_USD")
    assert 1.0026 == SL

datetimes = [(datetime.datetime(2018, 4, 27, 22, 0, 0),
              datetime.datetime(2020, 4, 27, 21, 0, 0), "short"),
             (datetime.datetime(2018, 5, 18, 21, 0, 0),
              datetime.datetime(2020, 3, 18, 21, 0, 0), "long"),
             (datetime.datetime(2018, 6, 17, 21, 0, 0),
              datetime.datetime(2020, 1, 17, 21, 0, 0), "long"),
             (datetime.datetime(2018, 7, 11, 21, 0, 0),
              datetime.datetime(2019, 8, 11, 21, 0, 0), "long"),
             (datetime.datetime(2018, 1, 9, 21, 0, 0),
              datetime.datetime(2019, 1, 9, 21, 0, 0), "short")]


@pytest.mark.parametrize("start,"
                         "end,"
                         "type",
                         datetimes
                         )
def test_get_trade_type(start, end, type, clO_pickled):
    new_cl = clO_pickled.slice(start=start,
                               end=end)

    assert type == get_trade_type(end, new_cl)

def test_adjust_SL_candles_short(clO_pickled):
    """Test adjust_SL_candles function with a short trade"""
    start = datetime.datetime(2018, 9, 2, 21, 0)
    end = datetime.datetime(2020, 9, 2, 21, 0)
    subClO = clO_pickled.slice(start=start, end=end)
    SL = adjust_SL_candles("short", subClO)

    assert SL == 0.74138


def test_adjust_SL_candles_long(clO_pickled):
    """Test adjust_SL_candles function with a short trade"""
    start = datetime.datetime(2019, 9, 28, 21, 0)
    end = datetime.datetime(2020, 9, 28, 21, 0)
    subClO = clO_pickled.slice(start=start, end=end)
    SL = adjust_SL_candles("long", subClO)

    assert SL == 0.70061

def test_adjust_SL_nextSR(halist_factory):
    SL, TP = adjust_SL_nextSR(halist_factory, 2, "short")
    assert SL == 0.67
    assert TP == 0.63

