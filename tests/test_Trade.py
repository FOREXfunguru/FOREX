import pytest

from TradeJournal import TradeJournal

@pytest.fixture
def tj_object():
    '''Returns a TradeJournal object'''
    '''
    td=TradeJournal(url="data/Trading_journal_07082017.xlsx")
    '''

    td=TradeJournal(url="data/test.xlsx")
    return td
'''
def test_fetch_trades(tj_object):

    trade_list=tj_object.fetch_trades()
    
    assert len(trade_list)==86
    assert trade_list[0].start.strftime('%Y-%m-%d')=='2017-03-20'
    assert trade_list[0].end.strftime('%Y-%m-%d')=='2017-03-23'
    assert trade_list[0].pair=='AUD_NZD'
    assert trade_list[0].timeframe=='H12'
    assert trade_list[0].type=='short'
'''
def test_add_trend_momentum(tj_object):

    tj_object.add_trend_momentum()

    assert 0


