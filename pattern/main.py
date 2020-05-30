from trade_journal.trade_journal import TradeJournal

import argparse
import pdb

def main():
    parser = argparse.ArgumentParser(description='Script to calculate the features for Counter trades')

    parser.add_argument('--ifile', required=True, help='.xlsx files with the trades')
    parser.add_argument('--worksheet', required=True, help='Worksheet from --ifile that will be analyzed')
    parser.add_argument('--settingf', required=True, help='Path to .ini file with settings')

    args = parser.parse_args()

    td = TradeJournal(url=args.ifile, worksheet=args.worksheet, settingf=args.settingf)

    trade_list = td.fetch_tradelist()
    trade_list.analyze()

    td.write_tradelist(trade_list)


if __name__ == '__main__':
    main()
