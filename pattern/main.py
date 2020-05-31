from trade_journal.trade_journal import TradeJournal

import argparse
import pdb
import logging

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(description='Script to calculate the features for Counter trades')

    parser.add_argument('--ifile', required=True, help='.xlsx files with the trades')
    parser.add_argument('--worksheet', required=True, help='Worksheet from --ifile that will be analyzed')
    parser.add_argument('--settingf', required=True, help='Path to .ini file with settings')

    args = parser.parse_args()

    logger.info("Creating TradeJournal")
    td = TradeJournal(url=args.ifile, worksheet=args.worksheet, settingf=args.settingf)
    logger.info("Done creating TradeJournal")

    trade_list = td.fetch_tradelist()
    logger.info("Analysing TradeList")
    trade_list.analyze()
    logger.info("Done TradeList")
    td.write_tradelist(trade_list)


if __name__ == '__main__':
    main()
