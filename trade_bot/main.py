from trade_bot import TradeBot
from trade_journal.trade_journal import TradeJournal
import pdb
import os
import argparse
import logging

# create logger
main_logger = logging.getLogger(__name__)
main_logger.setLevel(logging.INFO)

# The notifier function
def notify(title, subtitle, message):
    t = '-title {!r}'.format(title)
    s = '-subtitle {!r}'.format(subtitle)
    m = '-message {!r}'.format(message)
    os.system('terminal-notifier {}'.format(' '.join([m, t, s])))

def main():
    parser = argparse.ArgumentParser(description='Trading bot')

    parser.add_argument('--pair', required=True, help="Pair to be analysed: EUR_GBP")
    parser.add_argument('--timeframe', required=True, help="Timeframe used: i.e. 'D', 'H12', 'H8'")
    parser.add_argument('--start', required=True, help="Start time for this bot: i.e. 2019-08-12 22:00:00")
    parser.add_argument('--end', required=True, help="End time for this bot: i.e. 2019-08-19 22:00:00")
    parser.add_argument('--url', required=True, help=".xlsx file used to write the Trades taken")
    parser.add_argument('--ser_data_f', help="Serialized file with candle data")
    parser.add_argument('--settingf', required=True, help='Path to .ini file with settings')

    args = parser.parse_args()

    tb = TradeBot(
        pair=args.pair,
        timeframe=args.timeframe,
        start=args.start,
        end=args.end,
        ser_data_f=args.ser_data_f,
        settingf=args.settingf)

    main_logger.info("Running TradeBot")
    pickled_file = "{0}.pckl".format(os.path.basename(args.url).split('.')[0])
    tl = tb.run(pickled_file=pickled_file)

    main_logger.info("Done TradeBot")

    if tl is not None:
        td = TradeJournal(url=args.url,
                          worksheet="trading_journal",
                          settingf=args.settingf)
        td.write_tradelist(tl)
    else:
        main_logger.info("No trades found. No worksheet will be created in tradejournal")



if __name__ == '__main__':
    main()
    # Calling the function
    notify(title='A main.py TradeBot notification',
           subtitle='with python',
           message='Hello, this is me, notifying you that script has finished!')

