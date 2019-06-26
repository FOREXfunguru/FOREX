from oanda_api import OandaAPI
from candlelist import CandleList
import argparse

parser = argparse.ArgumentParser(description='Script to calculate some basis stats on the trend momentum of a Candle List ranging from a certain timepoint to the current time')
parser.add_argument('--instrument', type=str, required=True, help='Instrument used for retrieving the Candle List. i.e. AUD_USD or EUR_USD' )
parser.add_argument('--granularity', type=str, required=True, help='Timeframe used. i.e. D, H12,H8,H4 ' )
parser.add_argument('--start', type=str, required=True, help='Start time. i.e. 2017-12-13T08:00:00' )
parser.add_argument('--end', type=str, required=False, help='End time. If defined, do the analysis for time period between start and end' )
parser.add_argument('--trade_type', type=str, required=True, help='Type of trade. Possible values are short, long' )


args = parser.parse_args()

oanda=None
if args.end is not None:
    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument=args.instrument,
                   granularity=args.granularity,
                   alignmentTimezone='Europe/London',
                   dailyAlignment=22,
                   start=args.start,
                   end=args.end
                   )
else:
    oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                   instrument=args.instrument,
                   granularity=args.granularity,
                   alignmentTimezone='Europe/London',
                   dailyAlignment=22,
                   start=args.start)

candle_list=oanda.fetch_candleset()

trade_type=str(args.trade_type)
cl=CandleList(candle_list, type=trade_type)
cl.calc_binary_seq(merge=True)
cl.calc_number_of_0s(norm=True)
cl.calc_number_of_doubles0s(norm=True)
cl.calc_longest_stretch()

for k in cl.seq:
    print("\t{0}: {1}".format(k,cl.seq[k]))

print("Number of 0s (merged): %.2f" % cl.number_of_0s['merge'])
print("Double0s (highlow): {0}".format(cl.highlow_double0s))
print("Double0s (openclose): {0}".format(cl.openclose_double0s))
print("Stretch:")

for k in cl.longest_stretch:
    print("\t{0}: {1}".format(k,cl.longest_stretch[k]))
