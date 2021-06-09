import pytest
import os
import pdb

from trade_journal import TradeJournal
from pathlib import Path

@pytest.fixture
def clean_tmp():
    yield
    print("\nCleanup .xlsx file")
    os.remove(os.getenv('DATADIR')+"testCounter1.xlsx")

def test_fetch_trades(tjO):
    tlist = tjO.fetch_trades()

    assert len(tlist) == 4

def test_win_rate(tjO):

    (number_s, number_f, tot_pips) = tjO.win_rate(strats="counter")

    assert number_s == 2
    assert number_f == 1
    assert tot_pips == 274.5

def test_write_tradelist(t_object_list, clean_tmp):
    td = TradeJournal(url=os.getenv('DATADIR') + "/testCounter1.xlsx",
                      worksheet="trading_journal")

    td.write_tradelist(t_object_list, 'outsheet')

    assert os.path.exists(os.getenv('DATADIR') + "/testCounter1.xlsx") == 1
