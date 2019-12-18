import argparse
import pdb

from TradeJournal.tradejournal import TradeJournal

parser = argparse.ArgumentParser(description='Script to calculate the features for Counter trades')

parser.add_argument('--ifile', required=True, help='.xlsx files with the trades')
parser.add_argument('--worksheet', required=True, help='Worksheet from --ifile that will be analyzed')
parser.add_argument('--strat', required=True, help='Strategy in --worksheet to be analyzed')

args = parser.parse_args()

td = TradeJournal(url=args.ifile, worksheet=args.worksheet)

trade_list = td.fetch_trades(strat=args.strat,run=True)

td.write_trades(trade_list, colnames=['id', 'start', 'strat', 'type', 'SMA', 'entry', 'TP', 'SL', 'SR','entry_time','outcome','pips','lasttime',
                                      'bounces','bounces_lasttime'], sheetname= args.strat+".calc")
#td.write_trades(trade_list, colnames=['id', 'start', 'strat', 'type', 'SMA', 'entry', 'TP', 'SL', 'SR','entry_time','outcome','pips'], sheetname= args.strat+".calc")

