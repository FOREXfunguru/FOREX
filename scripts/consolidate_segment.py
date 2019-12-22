from oanda_api import OandaAPI
from candlelist import CandleList

oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='EUR_NZD',
                     granularity='D',
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22)

oanda.run(start='2014-11-26T22:00:00',
              end='2015-09-21T22:00:00',
              roll=True)

candle_list2 = oanda.fetch_candleset()

cl2 = CandleList(candle_list2, instrument='EUR_NZD', type='long')

pl2 = cl2.get_pivotlist(outfile='cl2_0_02_a.png', th_up=0.02, th_down=-0.02)

slist2 = pl2.slist

mslist2=slist2.merge_segments(min_n_candles=30, diff_in_pips=400, outfile="mcl2_0_01_ncandles20c.png")