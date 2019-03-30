import argparse
import pdb
import datetime

from CandleList import CandleList
from OandaAPI import OandaAPI
from TradeJournal.TradeJournal import TradeJournal
from HArea import HArea

parser = argparse.ArgumentParser(description='Script to calculate features for different Trades recorded in a Trade journal')

parser.add_argument('--ifile', required=True, help='Excel spreadsheet with trades')

args = parser.parse_args()

td=TradeJournal(url=args.ifile, worksheet='trading_journal')

def process_counter_dbtp(t,period=1000):
    '''
    Process trades of strat='counter_dbtp'

    Parameters
    ----------
    t
    period : int
            Period that will be checked back in time. Units used will be the ones dictated by t.timeframe.
            Default : 1000
    '''

    delta=None
    delta_1=None
    if t.timeframe == "D":
        delta_period = datetime.timedelta(days=period)
        delta_1 = datetime.timedelta(days=1)
    else:
        fgran = self.granularity.replace('H', '')
        delta_period = datetime.timedelta(hours=int(fgran)*period)
        delta_1 = datetime.timedelta(hours=int(fgran))

    start=t.start-delta_period
    end=t.start+delta_1

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument=t.pair,
                     granularity=t.timeframe,
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22,
                     start=start.isoformat(),
                     end=end.isoformat())

    candle_list = oanda.fetch_candleset()

    close_prices = []
    datetimes = []
    for c in oanda.fetch_candleset():
        close_prices.append(c.closeAsk)
        datetimes.append(c.time)

    resist = HArea(price=t.SR, pips=100, instrument=t.pair, granularity=t.timeframe)

    (bounces, outfile) = resist.number_bounces(datetimes=datetimes,
                                               prices=close_prices,
                                               min_dist=5
                                               )

    if t.type=="short": position='above'
    if t.type=="long": position = 'below'

    cl = CandleList(candle_list, instrument=t.pair, granularity=t.timeframe)

    last_time=resist.last_time(clist=cl, position=position)
    pdb.set_trace()
    print("h")


trade_list=td.fetch_trades()

for t in trade_list:
    if t.strat=='counter_dbtp':
        process_counter_dbtp(t)
    print(t)