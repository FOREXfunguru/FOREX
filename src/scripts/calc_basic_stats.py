import argparse
import pdb

from TradeJournal.TradeJournal import TradeJournal

parser = argparse.ArgumentParser(description='Script to calculate some basic stats on the Trading journal')

parser.add_argument('--ifile', required=True, help='.xlsx files with the trades')

args = parser.parse_args()

td = TradeJournal(url=args.ifile, worksheet='backtesting_taken_false')

td.print_winrate(strat='counter_doubletop')