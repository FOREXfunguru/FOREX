from apis.oanda_api import OandaAPI
from candle.candlelist import CandleList

oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='AUD_USD',
                     granularity='D',
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22)

oanda.run(start='2015-06-24T22:00:00',
              end='2019-06-21T22:00:00',
              roll=True)

candle_list2 = oanda.fetch_candleset()

cl2 = CandleList(candle_list2, instrument='AUD_USD', type='long')

pl2 = cl2.get_pivotlist(outfile='pre.png', th_up=0.02, th_down=-0.02)

slist2 = pl2.slist
mslist2=slist2.merge_segments(min_n_candles=8, diff_in_pips=1000000, outfile="caca.png")