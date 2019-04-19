import argparse
import pdb

from TradeJournal.TradeJournal import TradeJournal


parser = argparse.ArgumentParser(description='Script to calculate the features for Counter DoubleTop trades')

parser.add_argument('--ifile', required=True, help='.xlsx files with the trades')

args = parser.parse_args()

td = TradeJournal(url=args.ifile, worksheet='counter_doubletop')

trade_list = td.fetch_trades(strat='counter_doubletop',run=True)

print("h")