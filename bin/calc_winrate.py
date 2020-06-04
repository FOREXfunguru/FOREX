import argparse
import logging
import argparse
import pdb

from trade_journal.trade_journal import TradeJournal

parser = argparse.ArgumentParser(description='calc win rate on a Trading journal')

parser.add_argument('--tj', required=True, help=".xlsx file containing the Trading Journal")
parser.add_argument('--ws', required=True, help="Worksheet in --tj to be analysed")
parser.add_argument('--strats', required=True, help="Comma-separated list of strategies to analyse: i.e."
                                                    "counter,counter_b1")
parser.add_argument('--settingf', required=True, help='Path to .ini file with settings')

args = parser.parse_args()

td = TradeJournal(url=args.tj,
                  worksheet=args.ws,
                  settingf=args.settingf)

trade_list = td.fetch_tradelist()

trade_list.win_rate(strats=args.strats)