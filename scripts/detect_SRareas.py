import argparse
import numpy as np
import pandas as pd
from utils import *
from TradeJournal.trade import Trade

import pdb

from Pattern.counter import Counter

parser = argparse.ArgumentParser(description='Script to detect SR areas for a particular instrument/granularity')

parser.add_argument('--instrument', required=True, help='Instrument')
parser.add_argument('--granularity', required=True, help='Granularity')
parser.add_argument('--start', required=True, help='Start time to detect SR areas in isoformat. Example: 2019-03-08 22:00:00')
parser.add_argument('--ul', required=True, help='Upper limit of the range of prices')
parser.add_argument('--ll', required=True, help='Lower limit of the range of prices')
parser.add_argument('--th', required=True, help='Sensitivity threshold for filtering S/R lines')
parser.add_argument('--settingf', required=True, help='Path to .ini file with settings')

args = parser.parse_args()

# out file
scoref_name = "out_scores.{0}.txt".format(args.th)
file = open(scoref_name, 'w')

prices = []
bounces = [] #contains the number of pivots per price level
score_per_bounce = []
tot_scores = []
file.write("#price\tn_bounces\ttot_score\tscore_per_bounce\n")

# the increment of price in number of pips is double the hr_extension
prev_p = None
p = float(args.ll)
while p <= float(args.ul):
    print("Processing S/R at {0}".format(round(p, 4)))
    # each of 'p' will become a S/R that will be tested for bounces
    # set entry to price+30pips
    entry = add_pips2price(args.instrument, p, 30)
    # set S/L to price-30pips
    SL = substract_pips2price(args.instrument, p, 30)
    t = Trade(
        id='{0}.detect_sr.{1}'.format(args.instrument, round(p, 5)),
        start=args.start,
        pair=args.instrument,
        timeframe='D',
        type='short',
        entry=entry,
        SR=p,
        SL=SL,
        RR=1.5,
        strat='counter_b1',
        settingf=args.settingf)

    c = Counter(
        trade=t,
        init_feats=True,
        settingf=args.settingf
    )

    ratio = None
    if len(c.pivots.plist) == 0:
        ratio = 0
        mean_pivot = 0
    else:
        mean_pivot = round(c.score_pivot, 2)
    file.write("{0}\t{1}\t{2}\t{3}\n".format(round(p, 5), len(c.pivots.plist),
                                             c.total_score, mean_pivot))

    prices.append(round(p, 5))
    bounces.append(len(c.pivots.plist))
    tot_scores.append(c.total_score)
    score_per_bounce.append(mean_pivot)
    p = add_pips2price(args.instrument, p, 60)
    if prev_p is None:
        prev_p = p
    else:
        increment_price = round(p-prev_p, 5)
        prev_p = p

file.close()

data = {'price': prices,
        'bounces': bounces,
        'scores': score_per_bounce,
        'tot_scores': tot_scores}

df = pd.DataFrame(data=data)
### establishing bounces threshold as the args.th quantile
# selecting only rows with at least one pivot and tot_score>0, so threshold selection considers only these rows
# and selection is not biased when range of prices is wide
dfgt1 = df.loc[(df['bounces'] > 0)]
dfgt2 = df.loc[(df['tot_scores'] > 0)]
bounce_th = dfgt1.bounces.quantile(float(args.th))
score_th = dfgt2.tot_scores.quantile(float(args.th))
print("Selected number of pivot threshold: {0}".format(bounce_th))
print("Selected tot score threshold: {0}".format(score_th))

# selecting records over threshold
dfsel = df.loc[(df['bounces'] > bounce_th) | (df['tot_scores'] > score_th)]

def calc_diff(df_loc):

    prev_price = None
    prev_row = None
    prev_ix = None
    tog_seen = False
    for index, row in df_loc.iterrows():
        if prev_price is None:
            prev_price = float(row['price'])
            prev_row = row
            prev_ix = index
        else:
            diff = round(float(row['price'])-prev_price, 4)
            if diff < 3*increment_price:
           # if diff <= 0.035:
                tog_seen = True
                if row['bounces'] <= prev_row['bounces'] and row['tot_scores'] < prev_row['tot_scores']:
                    #remove current row
                    df_loc.drop(index, inplace=True)
                elif row['bounces'] >= prev_row['bounces'] and row['tot_scores'] > prev_row['tot_scores']:
                    #remove previous row
                    df_loc.drop(prev_ix, inplace=True)
                    prev_price = float(row['price'])
                    prev_row = row
                    prev_ix = index
                elif row['bounces'] <= prev_row['bounces'] and row['tot_scores'] > prev_row['tot_scores']:
                    #remove previous row as scores in current takes precedence
                    df_loc.drop(prev_ix, inplace=True)
                    prev_price = float(row['price'])
                    prev_row = row
                    prev_ix = index
                elif row['bounces'] >= prev_row['bounces'] and row['tot_scores'] < prev_row['tot_scores']:
                    #remove current row as scores in current takes precedence
                    df_loc.drop(index, inplace=True)
                elif row['bounces'] == prev_row['bounces'] and row['tot_scores'] == prev_row['tot_scores']:
                    #exactly same quality for row and prev_row
                    #remove current arbitrarily
                    df_loc.drop(index, inplace=True)
            else:
                prev_price = float(row['price'])
                prev_row = row
                prev_ix = index
    return df_loc, tog_seen

#repeat until no overlap between prices
ret = calc_diff(dfsel)
dfsel = ret[0]
tog_seen = ret[1]
while tog_seen is True:
    ret = calc_diff(dfsel)
    dfsel = ret[0]
    tog_seen = ret[1]

#write final DF to file
outfname = 'selected_SRareas.{0}.csv'.format(args.th)
export_csv = dfsel.to_csv(outfname, index=None,
                          header=True, sep='\t')
