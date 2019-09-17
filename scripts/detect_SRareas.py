from oanda_api import OandaAPI
from datetime import *
from utils import *
import config
import warnings
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

def estimate_bounces(price):
    '''
    Function to estimate the bounces at 'price'

    Parameters
    ----------
    price: float
           Price used to identify bounces

    Returns
    -------
    list List with bounces
    '''

    hr = HArea(price=price,
               pips=100,
               instrument=args.instrument,
               granularity=args.granularity)


    inarea_bounces = hr.inarea_bounces(plist=plist)
    if len(inarea_bounces)>1:
        inarea_cl = CandleList(inarea_bounces, instrument=args.instrument, granularity=args.granularity)
        inarea_bounces = inarea_cl.improve_resolution(part='openAsk', price=price)

    return inarea_bounces

def calc_surr_lengths(b_list):
    '''
    Function to calculate the number of candles of
    segments around each bounce

    Parameters
    ----------
    blist: List of candles representing each bounce
    '''

    if len(b_list)==0:
        warnings.warn("No bounces in area. Skipping...")
        return 0

    delta_period = periodToDelta(100, args.granularity)

    for b in b_list:
        pdb.set_trace()
        # get 50 candles after and before the bounce
        start = b.time - delta_period
        end = b.time + delta_period
        sub_cl=cl.slice(start,end)
        sub_pl = sub_cl.get_pivotlist(outfile='test.png', th_up=0.01, th_down=-0.01)
        slist = sub_pl.slist

        mslist=slist.merge_segments(min_n_candles=5, diff_in_pips=100, outfile="test1.png")
        print("h")


bounce_dict={}
for p in np.arange(0.67985, 0.72219, 0.0001):
    inarea_bs=estimate_bounces(price=p)
    if len(inarea_bs)>0:
        calc_surr_lengths(inarea_bs)
        bounce_dict[p]=len(inarea_bs)

bounce_dict_sorted = {k: v for k, v in sorted(bounce_dict.items(), key=lambda x: x[1])}
pdb.set_trace()
print("h")

