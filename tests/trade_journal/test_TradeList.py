import pytest
import datetime

from trade_journal import TradeJournal

@pytest.fixture
def tlist_o():
    '''Returns a TradeList object using the trade_journal.fetch_tradelist() function'''

    td = TradeJournal(url="data/testCounter.xlsx",
                      worksheet="trading_journal",
                      settingf="data/settings.ini")

    trade_list = td.fetch_tradelist()
    return trade_list

def test_analyze(tlist_o):
    '''
    This test will check that the 'analyze' function works and
    the lasttime attribute for Counter has been added to a Trade
    in the TradeList
    '''

    tlist_o.analyze()
    assert datetime.datetime(2016, 6, 23, 9, 0) == (getattr(tlist_o.tlist[0], 'lasttime'))

def test_win_rate(tlist_o):

    (number_s, number_f, tot_pips) = tlist_o.win_rate(strats="counter")

    assert number_s == 2
    assert number_f == 0
    assert tot_pips == 349.2
