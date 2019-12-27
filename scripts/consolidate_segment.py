from oanda_api import OandaAPI
from candlelist import CandleList

oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='GBP_AUD',
                     granularity='D',
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22)

oanda.run(start='2016-04-27T22:00:00',
              end='2018-10-11T22:00:00',
              roll=True)

candle_list2 = oanda.fetch_candleset()

cl2 = CandleList(candle_list2, instrument='EUR_NZD', type='long')

pl2 = cl2.get_pivotlist(outfile='pre.png', th_up=0.02, th_down=-0.02)

slist2 = pl2.slist
mslist2=slist2.merge_segments(min_n_candles=10, diff_in_pips=1000000, outfile="caca.png")