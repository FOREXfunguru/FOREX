import pytest

from trading_journal.trade import UnawareTrade
from trading_journal.trade_journal import TradeJournal
from utils import DATA_DIR


@pytest.fixture
def t_object(clO_pickled):
    """Returns a UnawareTrade object"""

    td = UnawareTrade(
        start="2017-04-10 14:00:00",
        end="2017-04-26 14:00:00",
        entry=0.74960,
        TP=0.75592,
        SL=0.74718,
        SR=0.74784,
        pair="AUD_USD",
        type="long",
        timeframe="D",
        clist=clO_pickled,
        clist_tm=clO_pickled)
    return td


@pytest.fixture
def t_object_list(clO_pickled):
    """Returns a list of UnawareTrade objects"""

    td = UnawareTrade(
        start="2017-04-10 14:00:00",
        end="2017-04-26 14:00:00",
        entry=0.74960,
        TP=0.75592,
        SL=0.74718,
        SR=0.74784,
        pair="AUD_USD",
        type="long",
        timeframe="H8",
        strat="counter_b1",
        id="AUD_USD 10APR2017H8",
        clist=clO_pickled,
        clist_tm=clO_pickled)
    return [td]


@pytest.fixture
def tjO(scope="session"):
    """Returns a trade_journal object for a Counter trade"""
    td = TradeJournal(url=DATA_DIR+"/testCounter.xlsx",
                      worksheet="trading_journal")
    return td
