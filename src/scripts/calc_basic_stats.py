import argparse
import pdb

from TradeJournal.tradejournal import TradeJournal

parser = argparse.ArgumentParser(description='Script to calculate some basic stats on the Trading journal')

parser.add_argument('--ifile', required=True, help='.xlsx files with the trades')
parser.add_argument('--sheet', required=True, help='Worksheet in the .xlsx that will be analyzed')
parser.add_argument('--strat', required=False, help='Trade strat that will be analyzed')
parser.add_argument('--wsname', required=False, help='Worksheet name')

args = parser.parse_args()

td = TradeJournal(url=args.ifile, worksheet=args.sheet)

(prop,pips,number)=td.print_winrate(strat=args.strat, write_xlsx=True, worksheet_name=args.wsname)

print("Total number of records:\n{0}".format(number))
print("Proportion:\n{0}".format(prop))
print("Sum of pips:{0}".format(pips))
