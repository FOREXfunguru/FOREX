import argparse
import pdb

from TradeJournal.TradeJournal import TradeJournal


parser = argparse.ArgumentParser(description='Script to calculate the features for Counter DoubleTop trades')

parser.add_argument('--ifile', required=True, help='.xlsx files with the trades')

args = parser.parse_args()

td = TradeJournal(url=args.ifile, worksheet='counter_doubletop')

trade_list = td.fetch_trades(strat='counter_doubletop',run=True)

td.write_trades(trade_list, colnames=['id', 'start', 'strat', 'entry', 'entry_time','outcome',
                                      'trend_i', 'type', 'timeframe', 'SR', 'TP',
                                      'SR', 'length_candles', 'length_pips',
                                      'n_rsibounces', 'rsibounces_lengths', 'bounces',
                                      'bounces_lasttime', 'entry_onrsi', 'last_time',
                                      'slope', 'divergence', 'bounce_1st', 'bounce_2nd',
                                      'rsi_1st', 'rsi_2nd', 'diff', 'valley','HR_pips'])

print("h")