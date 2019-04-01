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
        delta_period = datetime.timedelta(hours=24*period)
        delta_1 = datetime.timedelta(hours=24)
    else:
        fgran = t.timeframe.replace('H', '')
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

    cl = CandleList(candle_list, t.pair, granularity=t.timeframe)
    cl.calc_rsi(period=1000)

    close_prices = []
    datetimes = []
    for c in candle_list:
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

    bounces=[n for n in bounces if n[0] >= last_time]

    pdb.set_trace()

    #calc RSI for 1st and 2nd bounces

    inrsi_1st_bounce = False
    inrsi_2nd_bounce = False

    # 1st bounce
    cl_1st=cl.fetch_by_time((bounces[-2][0])
    if cl_1st.rsi>=70 or cl_1st.rsi<=70:
        inrsi_1st_bounce=True

    # 2nd bounce
    cl_2nd= cl.fetch_by_time(bounces[-1][0])
    if cl_2nd.rsi >= 70 or cl_2nd.rsi <= 70:
        inrsi_2nd_bounce = True

    #checking for feats in trend before 1st bounce
    oanda_1st_bounce=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument=t.pair,
                     granularity=t.timeframe,
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22,
                     start=t.trend_i.isoformat(),
                     end=bounces[-2][0].isoformat())

    candle_list1 = oanda_1st_bounce.fetch_candleset()

    cl1 = CandleList(candle_list1, instrument=t.pair, granularity=t.timeframe)

    (model, outfile) = cl1.fit_reg_line()

    direction = None
    if model.coef_[0, 0] > 0:
        direction = 'up'
    else:
        direction = 'down'

    print("h")


trade_list=td.fetch_trades()

for t in trade_list:
    if t.strat=='counter_dbtp':
        process_counter_dbtp(t)
    print(t)