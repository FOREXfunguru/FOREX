import argparse
import pdb
import datetime

from apis.oanda_api import OandaAPI

parser = argparse.ArgumentParser(description='Dump candle data to a file')

parser.add_argument('--pair', required=True, help="Pair to use. i.e. AUD_USD, EUR_GBP...")
parser.add_argument('--tf', required=True, help="Timeframe to use. i.e. D, H12, H8 ...")
parser.add_argument('--outfile', required=True, help="Output file to store the serialized data")
parser.add_argument('--settingf', required=True, help='Path to .ini file with settings')
parser.add_argument('--no_candles', required=True, help='Number of candles to slice')
parser.add_argument('--start', required=True, help='Datetime in format (2015-01-25T22:00:00) to start')
parser.add_argument('--end', required=True, help='Datetime in format (2015-01-25T22:00:00) to end')

args = parser.parse_args()

oanda = OandaAPI(instrument=args.pair,
                 granularity=args.tf,
                 settingf=args.settingf)

period = None
if args.tf == "D":
    period = 24
else:
    period = int(args.tf.replace('H', ''))

candles = []
startO = datetime.datetime.strptime(str(args.start), '%Y-%m-%dT%H:%M:%S')
endO = datetime.datetime.strptime(str(args.end), '%Y-%m-%dT%H:%M:%S')
while startO < endO:
    start = startO.isoformat()
    startO = startO+datetime.timedelta(hours=int(args.no_candles)*period)
    if startO >= endO:
        if startO > datetime.datetime.now():
            end = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        else:
            end = endO.isoformat()
    else:
        end = startO.isoformat()
    print("Processing: {0}-{1}".format(start, end))
    oanda.run(start=start,
              end=end)
    candles = candles+oanda.data['candles']
    startO = startO+datetime.timedelta(hours=1*period)

del oanda.data['candles']
oanda.data['candles'] = candles
oanda.serialize_data(outfile=args.outfile)
