import argparse
import pdb

from TradeJournal.tradejournal import TradeJournal

parser = argparse.ArgumentParser(description='Script to calculate the features for Counter trades')

parser.add_argument('--ifile', required=True, help='.xlsx files with the trades')

args = parser.parse_args()

td = TradeJournal(url=args.ifile, worksheet='backtesting_23102019')

#td.print_winrate(strat="counter_doubletop")

trade_list = td.fetch_trades(strat='counter',run=True)

td.write_trades(trade_list, colnames=['id', 'start', 'strat', 'entry', 'entry_time','outcome','lasttime',
                                      'bounces','bounces_lasttime'])
