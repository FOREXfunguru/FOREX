import pytest

from TradeJournal.TradeJournal import TradeJournal

@pytest.fixture
def tj_object():
    '''Returns a TradeJournal object'''

    td=TradeJournal(url="data/test.xlsx",worksheet='trading_journal')

    return td

def test_fetch_trades(tj_object):

    trade_list=tj_object.fetch_trades()
    
    assert len(trade_list)==1
    assert trade_list[0].start.strftime('%Y-%m-%d')=='2017-04-20'
    assert trade_list[0].end.strftime('%Y-%m-%d')=='2017-04-26'
    assert trade_list[0].pair=='AUD_USD'
    assert trade_list[0].timeframe=='H8'
    assert trade_list[0].type=='long'

def test_add_trend_momentum(tj_object):

    tj_object.add_trend_momentum()

    assert 1


