from trade_bot import TradeBot
from trade_journal.trade_journal import TradeJournal
import pdb
import argparse


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

    td = TradeJournal(url=args.url,
                      worksheet="trading_journal",
                      settingf=args.settingf)

    td.write_tradelist(tl)
    pdb.set_trace()
    print("h\n")


if __name__ == '__main__':
    main()
