from TradeJournal.tradejournal import TradeJournal
import pdb

td=TradeJournal(url="../tests/data/Trading_journal_07082017.xlsx",worksheet='combined')

td.add_trend_momentum()
