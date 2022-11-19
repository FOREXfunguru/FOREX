from forex.params import tradebot_params, clist_params, pivots_params
from forex.harea import HArea, HAreaList
from utils import *

import logging
import pandas as pd

# create logger
cl_logger = logging.getLogger(__name__)
cl_logger.setLevel(logging.INFO)

def calc_SR(pvLO, outfile: str):
    """Function to calculate S/R lines.

    Args:
        pvlO: PivotList object
              used for calculation
        outfile : Output filename for .png file

    Returns:
        HAreaList object
    """
    ## now calculate the price range for calculating the S/R , add a number of pips to max,min to be sure that we
    # also detect the extreme pivots
    ul = add_pips2price(pvLO.clist.instrument, pvLO.clist.get_highest(), tradebot_params.add_pips)
    ll = substract_pips2price(pvLO.clist.instrument, pvLO.clist.get_lowest(), tradebot_params.add_pips)

    cl_logger.debug("Running calc_SR for estimated range: {0}-{1}".format(ll, ul))

    prices, bounces, score_per_bounce, tot_score = ([] for i in range(4))

    # the increment of price in number of pips is double the hr_extension
    prev_p = None

    p = float(ll)

    while p <= float(ul):
        cl_logger.debug("Processing S/R at {0}".format(round(p, 4)))
        # get a PivotList for this particular S/R
        newPL = pvLO.inarea_pivots(price=p)
        if len(newPL.pivots) == 0:
            mean_pivot = 0
        else:
            mean_pivot = newPL.get_avg_score()

        prices.append(round(p, 5))
        bounces.append(len(newPL.pivots))
        tot_score.append(newPL.get_score())
        score_per_bounce.append(mean_pivot)
        # increment price to following price. Because the increment is made in pips
        # it does not suffer of the JPY pairs issue
        p = add_pips2price(pvLO.clist.instrument, p,
                           2*clist_params.i_pips)
        if prev_p is None:
            prev_p = p
        else:
            increment_price = round(p - prev_p, 5)
            prev_p = p

    data = {'price': prices,
            'bounces': bounces,
            'scores': score_per_bounce,
            'tot_score': tot_score}

    df = pd.DataFrame(data=data)

    ### establishing bounces threshold as the args.th quantile
    # selecting only rows with at least one pivot and tot_score>0,
    # so threshold selection considers only these rows
    # and selection is not biased when range of prices is wide
    dfgt1 = df.loc[(df['bounces'] > 0)]
    dfgt2 = df.loc[(df['tot_score'] > 0)]
    bounce_th = dfgt1.bounces.quantile(tradebot_params.th)
    score_th = dfgt2.tot_score.quantile(tradebot_params.th)

    print("Selected number of pivot threshold: {0}".format(bounce_th))
    print("Selected tot score threshold: {0}".format(round(score_th,1)))

    # selecting records over threshold
    dfsel = df.loc[(df['bounces'] > bounce_th) | (df['tot_score'] > score_th)]

    # repeat until no overlap between prices
    ret = calc_diff(dfsel, increment_price)
    dfsel = ret[0]
    tog_seen = ret[1]
    while tog_seen is True:
        ret = calc_diff(dfsel, increment_price)
        dfsel = ret[0]
        tog_seen = ret[1]

    # iterate over DF with selected SR to create a HAreaList
    halist = []
    for index, row in dfsel.iterrows():
        resist = HArea(price=row['price'],
                       pips=pivots_params.hr_pips,
                       instrument=pvLO.clist.instrument,
                       granularity=pvLO.clist.granularity,
                       no_pivots=row['bounces'],
                       tot_score=round(row['tot_score'], 5))
        halist.append(resist)

    halistObj = HAreaList(halist=halist)

    # Plot the HAreaList
    dt_str = pvLO.clist.candles[-1].time.strftime("%d_%m_%Y_%H_%M")
    print(dt_str)

    if pivots_params.plot is True:
        halistObj.plot(clO= pvLO.clist, outfile=outfile)

    cl_logger.info("Run done")

    return halistObj

def calc_atr(clO)->float:
    '''Function to calculate the ATR (average timeframe rate)
    This is the average candle variation in pips for the desired
    timeframe. The variation is measured as the abs diff
    (in pips) between the high and low of the candle

    Arguments:
        clO: CandleList object
             Used for calculation
    '''
    length, tot_diff_in_pips  = 0,0
    for c in clO.candles:
        diff = abs(c.h-c.l)
        tot_diff_in_pips = tot_diff_in_pips + float(calculate_pips(clO.instrument, diff))
        length += 1
    return round(tot_diff_in_pips/length, 3)

def calc_diff(df_loc, increment_price):
    '''
    Function to select the best S/R for areas that
    are less than 3*increment_price

    Parameters
    ----------
    df_loc : Pandas dataframe with S/R areas
    increment_price : float
                      This is the increment_price
                      between different price levels
                      in order to identify S/Rs

    Returns
    -------
    Pandas dataframe with selected S/R
    '''
    prev_price = prev_row = prev_ix = None
    tog_seen = False
    for index, row in df_loc.iterrows():
        if prev_price is None:
            prev_price = float(row['price'])
            prev_row = row
            prev_ix = index
        else:
            diff = round(float(row['price']) - prev_price, 4)
            if diff < 3 * increment_price:
                tog_seen = True
                if row['bounces'] <= prev_row['bounces'] and row['tot_score'] < prev_row['tot_score']:
                    # remove current row
                    df_loc.drop(index, inplace=True)
                elif row['bounces'] >= prev_row['bounces'] and row['tot_score'] > prev_row['tot_score']:
                    # remove previous row
                    df_loc.drop(prev_ix, inplace=True)
                    prev_price = float(row['price'])
                    prev_row = row
                    prev_ix = index
                elif row['bounces'] <= prev_row['bounces'] and row['tot_score'] > prev_row['tot_score']:
                    # remove previous row as scores in current takes precedence
                    df_loc.drop(prev_ix, inplace=True)
                    prev_price = float(row['price'])
                    prev_row = row
                    prev_ix = index
                elif row['bounces'] >= prev_row['bounces'] and row['tot_score'] < prev_row['tot_score']:
                    # remove current row as scores in current takes precedence
                    df_loc.drop(index, inplace=True)
                elif row['bounces'] == prev_row['bounces'] and row['tot_score'] == prev_row['tot_score']:
                    # exactly same quality for row and prev_row
                    # remove current arbitrarily
                    df_loc.drop(index, inplace=True)
            else:
                prev_price = float(row['price'])
                prev_row = row
                prev_ix = index
    return df_loc, tog_seen