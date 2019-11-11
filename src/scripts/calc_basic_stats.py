import argparse
import pdb

from TradeJournal.tradejournal import TradeJournal

parser = argparse.ArgumentParser(description='Script to calculate some basic stats on the Trading journal')

parser.add_argument('--ifile', required=True, help='.xlsx files with the trades')
parser.add_argument('--sheet', required=True, help='Worksheet in the .xlsx that will be analyzed')
parser.add_argument('--strat', required=True, help='Trade strat that will be analyzed')

args = parser.parse_args()

td = TradeJournal(url=args.ifile, worksheet='backtesting')

td.print_winrate(strat='counter_beftrade')