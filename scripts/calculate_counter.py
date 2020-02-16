import argparse
import pdb

from TradeJournal.tradejournal import TradeJournal

parser = argparse.ArgumentParser(description='Script to calculate the features for Counter trades')

parser.add_argument('--ifile', required=True, help='.xlsx files with the trades')
parser.add_argument('--worksheet', required=True, help='Worksheet from --ifile that will be analyzed')
parser.add_argument('--outsheet', required=True, help='Worksheet name for calculated trades')
parser.add_argument('--settings', required=True, help='Path to .ini file with settings')

args = parser.parse_args()

td = TradeJournal(url=args.ifile, worksheet=args.worksheet, settings=args.settings)

trade_list = td.fetch_trades(run=True)

td.write_trades(trade_list, sheetname=args.outsheet)

