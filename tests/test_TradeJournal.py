import pytest
import pdb

from TradeJournal.tradejournal import TradeJournal

@pytest.fixture
def tjO():
    '''Returns a TradeJournal object for a Counter trade'''

    td = TradeJournal(url="data/testCounter.xlsx",
                      worksheet="trading_journal",
                      settingf="data/settings.ini")
    return td

def test_fetch_tradelist(tjO):
    trade_list = tjO.fetch_tradelist()

    assert len(trade_list.tlist) == 1

def test_write_tradelist(tjO):
    trade_list = tjO.fetch_tradelist()

    tjO.write_tradelist(trade_list)

    assert 0
"""
    
def test_print_winrate(tj_counter_doubletop_object):
    trade_list = tj_counter_doubletop_object.print_winrate(strat='counter_doubletop')
"""