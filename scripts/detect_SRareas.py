from oanda_api import OandaAPI
from datetime import *
from utils import *
import config
import pdb
from harea import HArea
from candlelist import CandleList
import argparse
import numpy as np

parser = argparse.ArgumentParser(description='Script to detect SR areas for a particular instrument/granularity')

parser.add_argument('--instrument', required=True, help='Instrument')
parser.add_argument('--granularity', required=True, help='Granularity')
parser.add_argument('--start', required=True, help='Start time to detect SR areas in isoformat. Example: 2019-03-08 22:00:00')


args = parser.parse_args()

oanda = OandaAPI(url=config.OANDA_API['url'],
                 instrument=args.instrument,
                 granularity=args.granularity,
                 alignmentTimezone=config.OANDA_API['alignmentTimezone'],
                 dailyAlignment=config.OANDA_API['dailyAlignment'])

delta_period=periodToDelta(config.SRarea['period'], args.granularity)
startObj = datetime.datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S")

start = startObj - delta_period # get the start datetime for this CandleList period
end = startObj

oanda.run(start=start.isoformat(),
          end=end.isoformat(),
          roll=True)

candle_list = oanda.fetch_candleset()

cl=CandleList(clist=candle_list, instrument=args.instrument, granularity=args.instrument)

plist = cl.get_pivotlist(th_down=config.SRarea['th_down'],
                         th_up=-config.SRarea['th_up'],
                         outfile="/Users/ernesto/PycharmProjects/FOREX/scripts/test.png")


merged_segs=plist.slist.merge_segments(outfile="test1.png")

def estimate_bounces(price):
    hr = HArea(price=price,
               pips=100,
               instrument=args.instrument,
               granularity=args.granularity)


    inarea_bounces = hr.inarea_bounces(plist=plist)
    if len(inarea_bounces)>1:
        pdb.set_trace()
        inarea_cl = CandleList(inarea_bounces, instrument=args.instrument, granularity=args.granularity)
        in_area_list = inarea_cl.improve_resolution(part='openAsk', price=price)
        print("h")

    return inarea_bounces

bounce_dict={}
for p in np.arange(0.67985, 0.72219, 0.0001):
    inarea_bs=estimate_bounces(price=p)
    bounce_dict[p]=len(inarea_bs)

bounce_dict_sorted = {k: v for k, v in sorted(bounce_dict.items(), key=lambda x: x[1])}
pdb.set_trace()
print("h")

