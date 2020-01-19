import argparse
import numpy as np
import pandas as pd
from utils import *
import pdb

from Pattern.counter import Counter


parser = argparse.ArgumentParser(description='Script to detect SR areas for a particular instrument/granularity')

parser.add_argument('--instrument', required=True, help='Instrument')
parser.add_argument('--granularity', required=True, help='Granularity')
parser.add_argument('--start', required=True, help='Start time to detect SR areas in isoformat. Example: 2019-03-08 22:00:00')
parser.add_argument('--ul', required=True, help='Upper limit of the range of prices')
parser.add_argument('--ll', required=True, help='Lower limit of the range of prices')


args = parser.parse_args()

file = open('out_scores.txt','w')

prices=[]
bounces=[]
score_per_bounce=[]
file.write("#price\tn_bounces\ttot_score\tscore_per_bounce\n")

increment_price=0.006
# the increment of price in number of pips is double the hr_extension
for p in np.arange(float(args.ll), float(args.ul), increment_price):

    print("Processing S/R at {0}".format(round(p,4)))
    #each of 'p' will become a S/R that will be tested for bounces
    #set entry to price+30pips
    entry=add_pips2price(args.instrument,p,30)
    #set S/L to price-30pips
    SL=substract_pips2price(args.instrument,p,30)

    c = Counter(
        id='detect_sr',
        start=args.start,
        pair=args.instrument,
        timeframe='D',
        type='short',
        period=5000,
        HR_pips=30,
        entry=entry,
        SR=p,
        SL=SL,
        RR=1.5,
        png_prefix='/Users/ernesto/projects/FOREX/CT/detectSR/test.{0}'.format(p))
    file.write("{0}\t{1}\t{2}\t{3}\n".format(round(p,5),len(c.bounces.plist),c.total_score,round(c.total_score/len(c.bounces.plist),2)))
    prices.append(round(p,5))
    bounces.append(len(c.bounces.plist))
    score_per_bounce.append(round(c.total_score/len(c.bounces.plist),2))

data={'prices': prices,
      'bounces': bounces,
      'scores': score_per_bounce}

df = pd.DataFrame(data=data)
pdb.set_trace()
# establishing bounces threshold as the 0.75 quantile
bounce_th=df.bounces.quantile(0.75)
score_th=df.scores.quantile(0.75)

# selecting records over threshold
dfsel=df.loc[(df['bounces']>bounce_th) | (df['scores']>score_th)]
file.close()


