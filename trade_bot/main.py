from trade_bot import TradeBot
from trade_journal.trade_journal import TradeJournal
import pdb
import os
import argparse


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
    parser.add_argument('--settingf', required=True, help='Path to .ini file with settings')

    args = parser.parse_args()

    tb = TradeBot(
        pair=args.pair,
        timeframe=args.timeframe,
        start=args.start,
        end=args.end,
        settingf=args.settingf
    )

    tl = tb.run()
    if tl is not None:
        td = TradeJournal(url=args.url,
                          worksheet="trading_journal",
                          settingf=args.settingf)
        td.write_tradelist(tl)


if __name__ == '__main__':
    main()
    # Calling the function
    notify(title='A main.py TradeBot notification',
           subtitle='with python',
           message='Hello, this is me, notifying you that script has finished!')

