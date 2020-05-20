import pytest
import os

from trade_journal.trade_journal import TradeJournal
from pathlib import Path

@pytest.fixture
def tjO():
    '''Returns a trade_journal object for a Counter trade'''

    td = TradeJournal(url="../../data/testCounter.xlsx",
                      worksheet="trading_journal",
                      settingf="../../data/settings.ini")
    return td

@pytest.fixture
def clean_tmp():
    yield
    print("\nCleanup .xlsx file")
    os.remove("../../data/testCounter1.xlsx")

def test_tj_nonexists(clean_tmp):
    '''Instantiates a trade_journal object when the .xlsx pointed by url does not exist'''

    fname = Path("../../data/testCounter1.xlsx")

    td = TradeJournal(url=fname,
                      worksheet="trading_journal",
                      settingf="../../data/settings.ini")

    # check that fname has been initialized

    assert fname.exists() is True

def test_fetch_tradelist(tjO):
    trade_list = tjO.fetch_tradelist()

    assert len(trade_list.tlist) == 4

def test_write_tradelist(tjO):
    trade_list = tjO.fetch_tradelist()
    trade_list.analyze()

    tjO.write_tradelist(trade_list)