from trade_journal.trade_journal import TradeJournal

import argparse
import pdb
import logging
from apis.ser_data_obj import ser_data_obj

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def main():
    parser = argparse.ArgumentParser(description='Script to calculate the features for Counter trades')

    parser.add_argument('--ifile', required=True, help='.xlsx files with the trades')
    parser.add_argument('--worksheet', required=True, help='Worksheet from --ifile that will be analyzed')
    parser.add_argument('--settingf', required=True, help='Path to .ini file with settings')
    parser.add_argument('--ser_data_f', help="Serialized file with candle data")

    args = parser.parse_args()
    logger.info("Creating TradeJournal")

    if args.ser_data_f is None:
        td = TradeJournal(url=args.ifile,
                          worksheet=args.worksheet,
                          settingf=args.settingf)
    else:
        td = TradeJournal(url=args.ifile,
                          worksheet=args.worksheet,
                          settingf=args.settingf,
                          ser_data_obj=ser_data_obj(ifile=args.ser_data_f))
    logger.info("Done creating TradeJournal")

    trade_list = td.fetch_tradelist()
    if len(trade_list.tlist)==0:
        raise Exception("No trades fetched from Tradejournal in {0}".format(args.ifile))
    logger.info("Analysing TradeList")
    trade_list.analyze()
    logger.info("Done TradeList")
    td.write_tradelist(trade_list)


if __name__ == '__main__':
    main()
