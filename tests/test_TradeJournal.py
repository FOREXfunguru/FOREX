import pytest
import pdb

from TradeJournal.tradejournal import TradeJournal

@pytest.fixture
def tj_counter_object():
    '''Returns a TradeJournal object for a Counter trade'''

    td = TradeJournal(url="data/testCounter.xlsx",
                      worksheet="trading_journal",
                      settingf="data/settings.ini")
    return td

def test_fetch_tradelist(tj_counter_object):
    trade_list = tj_counter_object.fetch_tradelist()

    assert len(trade_list.tlist) == 1
"""

def test_fetch_counter_doubletop_trades(tj_counter_doubletop_object):
    trade_list = tj_counter_doubletop_object.fetch_trades(strat='counter_doubletop')

    assert len(trade_list) == 1
    assert trade_list[0].start.strftime('%Y-%m-%d') == '2019-02-21'



def test_add_trend_momentum(tj_object):

    tj_object.add_trend_momentum()

    assert 1

def test_write_trades_counter(tj_counter_object):
    trade_list = tj_counter_object.fetch_trades(strat='counter',run=True)

    tj_counter_object.write_trades(trade_list, colnames=['id','start','strat','entry','outcome','trend_i','type','timeframe',
                                                         'SR','TP','SR','length_candles','length_pips',
                                                         'n_rsibounces','rsibounces_lengths','bounces',
                                                         'bounces_lasttime','entry_onrsi','last_time',
                                                         'slope','divergence'])

    assert 1

def test_write_trades_counterdoubletop(tj_counter_doubletop_object):
    trade_list = tj_counter_doubletop_object.fetch_trades(strat='counter_doubletop',run=True)

    tj_counter_doubletop_object.write_trades(trade_list, colnames=['id','start','strat','entry','outcome',
                                                                   'trend_i','type','timeframe','SR','TP',
                                                                   'SR','length_candles','length_pips',
                                                                   'n_rsibounces','rsibounces_lengths','bounces',
                                                                   'bounces_lasttime','entry_onrsi','last_time',
                                                                   'slope','divergence','bounce_1st','bounce_2nd',
                                                                   'rsi_1st','rsi_2nd','diff','valley'])

    assert 1
    
def test_print_winrate(tj_counter_doubletop_object):
    trade_list = tj_counter_doubletop_object.print_winrate(strat='counter_doubletop')
"""