import pytest
import pdb

from TradeJournal.TradeJournal import TradeJournal

@pytest.fixture
def tj_object():
    '''Returns a TradeJournal object'''

    td=TradeJournal(url="data/test.xlsx",worksheet='trading_journal')

    return td

@pytest.fixture
def tj_counter_object():
    '''Returns a TradeJournal object for a Counter trade'''

    td=TradeJournal(url="data/testCounter.xlsx",worksheet='trading_journal')

    return td

'''
def test_fetch_trades(tj_object):

    trade_list=tj_object.fetch_trades()

    assert len(trade_list)==1
    assert trade_list[0].start.strftime('%Y-%m-%d')=='2019-02-24'
    assert trade_list[0].pair=='GBP_AUD'
    assert trade_list[0].timeframe=='D'
'''
def test_fetch_counter_trades(tj_counter_object):
    trade_list = tj_counter_object.fetch_trades(strat='counter')

'''
def test_add_trend_momentum(tj_object):

    tj_object.add_trend_momentum()

    assert 1
'''

