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
import pandas as pd

parser = argparse.ArgumentParser(description='Script to detect SR areas for a particular instrument/granularity')

parser.add_argument('--instrument', required=True, help='Instrument')
parser.add_argument('--granularity', required=True, help='Granularity')
parser.add_argument('--start', required=True, help='Start time to detect SR areas in isoformat. Example: 2019-03-08 22:00:00')


args = parser.parse_args()


def estimate_bounces(price,plist):
    '''
    Function to estimate the bounces at 'price'

    Parameters
    ----------
    price: float
           Price used to identify bounces
    plist: PivotList
           object

    Returns
    -------
    list List with bounces
    '''

    hr = HArea(price=price,
               pips=hr_extension,
               instrument=args.instrument,
               granularity=args.granularity)

    print("upper: {0} - lower: {1}".format(hr.upper,hr.lower))


    inarea_bounces = hr.inarea_bounces(plist=plist)
    if len(inarea_bounces)>1:
        inarea_cl = CandleList(inarea_bounces, instrument=args.instrument, granularity=args.granularity)
        inarea_bounces = inarea_cl.improve_resolution(part='openAsk', price=price, min_dist=10)

    return inarea_bounces

def calc_surr_lengths(b_list):
    '''
    Function to calculate the number of candles of
    segments around each bounce

    Parameters
    ----------
    blist: List of candles representing each bounce

    Returns
    -------
    Dict of dicts: Each key will be the datetime of the bounce
                   and each value will be the number of candles
                   of the SegmentList before and after the bounce
    '''

    if len(b_list)==0:
        warnings.warn("No bounces in area. Skipping...")
        return 0

    bounce_lengths={}
    # 100 will be the period before/after the bounce that will be used
    delta_period = periodToDelta(200, args.granularity)

    for b in b_list:
        bounce_lengths[b.time]={}
        start = b.time - delta_period
        end = b.time + delta_period

        # run api query with new period
        oanda.run(start=start.isoformat(),
                  end=end.isoformat(),
                  roll=True)

        candle_list = oanda.fetch_candleset()
        sub_cl = CandleList(clist=candle_list, instrument=args.instrument, granularity=args.instrument)

        # get PivotList
        sub_pl = sub_cl.get_pivotlist(outfile='test_subcl.png', th_up=0.02, th_down=-0.02)
        # get SegmentList
        slist = sub_pl.slist
        # merge segments

        mslist=slist.merge_segments(min_n_candles=10, diff_in_pips=200, outfile="test_subcl1.png")

        diff=None # will store the difference in datetime between bounce.time and start of SegmentList
        pr_ms=None # will store previous SegmentList
        max_pr_ms=None
        c_ms=None
        # this for loop will be used to detect the SegmentList
        # for which the difference in time between the start
        # and bounce time is the least
        for ms in mslist:
            # iterate over each merged SegmentList
            if diff is None:
                pr_ms=ms
                diff= abs(ms.start-b.time)
            else:
                if abs(ms.start-b.time)<diff:
                    max_pr_ms=pr_ms
                    c_ms=ms
                    diff=abs(ms.start-b.time)
                pr_ms = ms
        bounce_lengths[b.time]={'pre': max_pr_ms.length(),
                                'after': c_ms.length()}

    return bounce_lengths

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

bounce_dict={}

hr_extension=10
increment_price=0.002
# the increment of price in number of pips is double the hr_extension
for p in np.arange(0.68612, 0.75548, increment_price):
    print("Price: {0}".format(p))
    inarea_bs=estimate_bounces(price=p, plist=plist)
    print("Length: {0}".format(len(inarea_bs)))
    if len(inarea_bs)>0:
        seg_lens=calc_surr_lengths(inarea_bs)
        bounce_dict[p]=seg_lens

ix=1
final_dict={}
for price in bounce_dict.keys():
    bounces=len(bounce_dict[price]) # bounces at this price
    for d,segs in bounce_dict[price].items():
        final_dict[ix]=[price,bounces,d,segs['pre'],segs['after']]
        ix+=1

df = pd.DataFrame.from_dict(final_dict, orient='index',columns=['price','n_bounces','datetime','pre','after'])

def calc_score(x):
    '''
    Function to calc the score for 'pre' and 'after'
    '''

    if x=="short":
        return 1
    elif x=="medium":
        return 2
    elif x=="long":
        return 3

df['pre_cat']=pd.cut(df['pre'], 3, labels=["short", "medium", "long"])
df['after_cat']=pd.cut(df['after'], 3, labels=["short", "medium", "long"])

df['seg_score_pre']=df['pre_cat'].apply(calc_score)
df['seg_score_aft']=df['after_cat'].apply(calc_score)

#convert categorical column to int
df[['seg_score_pre', 'seg_score_aft']] = df[['seg_score_pre', 'seg_score_aft']].astype(int)
#sum scores for pre and aft
df['tot_seg_score']=df['seg_score_pre']+df['seg_score_aft']

resDF=df.groupby(['price','n_bounces']).agg({'tot_seg_score': 'sum'})

resDF.sort_values(by='tot_seg_score',inplace=True,ascending=False)

print("h")


