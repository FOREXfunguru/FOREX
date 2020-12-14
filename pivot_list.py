from zigzag import *
from segment import SegmentList
from segment import Segment
from pivot import Pivot
from utils import substract_pips2price, add_pips2price
from config import CONFIG
from candle.candle import Candle
from ast import literal_eval

import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import logging

logging.basicConfig(level=logging.INFO)

# create logger
pl_logger = logging.getLogger(__name__)
pl_logger.setLevel(logging.INFO)

import pdb

class PivotList(object):
    '''
    Class that represents a list of Pivots as identified
    by the Zigzag indicator

    Class variables
    ---------------
    clist : CandleList object
            CandleList for this PivotList. Required
    parray : Array of 1s and -1s obtained directly using the Zigzag indicator. Optional
    plist : list of Pivot objects, Optional
            List of pivot objects obtained using the 'peak_valley_pivots' function from Zigzag indicator
    slist : SegmentList object, Optional
    '''

    def __init__(self, clist, parray=None, plist=None,
                 slist=None):

        self.clist = clist

        if parray is not None:
            # pivots_to_modes function from the Zigzag indicator
            modes = pivots_to_modes(parray)
            segs = [] # this list will hold the Segment objects
            plist_o = [] # this list will hold the Pivot objects
            pre_s = None # Variable that will hold pre Segments
            start_ix = end_ix = pre_i = None
            ix = 0
            for i in parray:
                if (i == 1 or i == -1) and start_ix is None:
                    # First pivot
                    start_ix = ix
                    pre_i = i
                elif (i == 1 or i == -1) and start_ix is not None:
                    end_ix=ix
                    if parray[start_ix+1] == 0:
                        submode = modes[start_ix+1:end_ix]
                    else:
                        submode = [modes[start_ix+1]]
                    #checking if all elements in submode are the same:
                    assert len(np.unique(submode).tolist()) == 1, "more than one type in modes"
                    # create Segment
                    s = Segment(type=submode[0],
                                count=end_ix-start_ix,
                                clist=clist.data['candles'][start_ix:end_ix],
                                instrument=clist.data['instrument'])
                    # create Pivot object
                    c_dict = clist.data['candles'][start_ix]
                    # add granularity to dict
                    c_dict['granularity'] = clist.data['granularity']
                    pobj = Pivot(type=pre_i,candle=c_dict,
                                 pre=pre_s, aft=s)
                    pobj.score = pobj.calc_score()
                    # Append it to list
                    plist_o.append(pobj)
                    # Append it to segs
                    segs.append(s)
                    start_ix = ix
                    pre_s = s
                    pre_i = i
                ix += 1
            # add last Pivot
            c_dict = clist.data['candles'][start_ix]
            c_dict['granularity'] = clist.data['granularity']
            l_pivot = Pivot(type=pre_i,
                                 candle=c_dict,
                                 pre=pre_s,
                                 aft=None)
            l_pivot.score = l_pivot.calc_score()
            plist_o.append(l_pivot)

            self.plist = plist_o
            self.slist = SegmentList(slist=segs,
                                     instrument=clist.data['instrument'])
        else:
            self.plist = plist
            self.slist = slist

    def fetch_by_time(self, d):
        '''
        Function to fetch a Pivot object using a
        datetime

        Parameters
        ----------
        d : Datetime object

        Returns
        -------
        Pivot object
              None if not Pivot found
        '''

        for p in self.plist:
            if p.candle['time'] == d:
                return p
        return None

    def fetch_by_type(self, type):
        '''
        Function to get all pivots from a certain type

        Parameters
        ----------
        type : int
               1 or -1

        Returns
        -------
        PivotList of the desired type
        '''

        pl = []
        for p in self.plist:
            if p.type == type:
                pl.append(p)

        return PivotList(plist=pl,
                         clist=self.clist,
                         slist=self.slist)

    def print_pivots_dates(self):
        '''
        Function to generate a list with the datetimes of the different Pivots in PivotList

        :return:
        List of datetimes
        '''

        datelist = []
        for p in self.plist:
            datelist.append(p.candle['time'])

        return datelist

    def get_score(self):
        '''
        Function to calculate the score after adding the score
        for each individual pivot

        returns
        -------
        float with score
        '''

        tot_score = 0
        for p in self.plist:
            tot_score += p.score

        return round(tot_score, 1)

    def inarea_pivots(self, SR, last_pivot=True):
        '''
        Function to identify the candles for which price is in the area defined
        by SR+HRpips and SR-HRpips

        Parameters
        ---------
        pivots: PivotList object
        SR: float
            price of the S/R area
        last_pivot: Boolean
                    If True, then the last pivot will be considered as it is part
                    of the setup. Default: True

        Returns
        -------
        PivotList with pivots that are in the area
        '''

        # get bounces in the horizontal SR area
        lower = substract_pips2price(self.clist.data['instrument'],
                                     SR,
                                     CONFIG.getint('pivots',
                                                   'hr_pips'))
        upper = add_pips2price(self.clist.data['instrument'],
                               SR,
                               CONFIG.getint('pivots',
                                             'hr_pips'))

        pl_logger.warn("SR U-limit: {0}; L-limit: {1}".format(round(upper, 4), round(lower, 4)))

        pl = []
        for p in self.plist:
            # always consider the last pivot in bounces.plist as in_area as this part of the entry setup
            if self.plist[-1].candle['time'] == p.candle['time'] and last_pivot is True:
                adj_t = p.adjust_pivottime(clistO=self.clist)
                # get new CandleList with new adjusted time for the end
                newclist = self.clist.slice(start=self.clist.data['candles'][0]['time'],
                                            end=adj_t)
                newp = newclist.get_pivotlist(CONFIG.getfloat('pivots', 'th_bounces')).plist[-1]
                if CONFIG.getboolean('counter', 'runmerge_pre') is True and newp.pre is not None:
                    newp.merge_pre(slist=self.slist,
                                   n_candles=CONFIG.getint('pivots', 'n_candles'),
                                   diff_th=CONFIG.getint('pivots', 'diff_th'))
                if CONFIG.getboolean('counter', 'runmerge_aft') is True and newp.aft is not None:
                    newp.merge_aft(slist=self.slist,
                                   n_candles=CONFIG.getint('pivots', 'n_candles'),
                                   diff_th=CONFIG.getint('pivots', 'diff_th'))
                pl.append(newp)
            else:
                part_list = ['close{0}'.format(CONFIG.get('general', 'bit'))]
                if p.type == 1:
                    part_list.append('high{0}'.format(CONFIG.get('general', 'bit')))
                elif p.type == -1:
                    part_list.append('low{0}'.format(CONFIG.get('general', 'bit')))

                # initialize candle features to be sure that midAsk or midBid are
                # initialized
                cObj = Candle(dict_data=p.candle)
                cObj.set_candle_features()
                p.candle = cObj.__dict__
                for part in part_list:
                    price = p.candle[part]
                    # only consider pivots in the area
                    if price >= lower and price <= upper:
                        # check if this pivot already exists in pl
                        p_seen = False
                        for op in pl:
                            if op.candle['time'] == p.candle['time']:
                                p_seen = True
                        if p_seen is False:
                            pl_logger.debug("Pivot {0} identified in area".format(p.candle['time']))
                            if CONFIG.getboolean('counter', 'runmerge_pre') is True and p.pre is not None:
                                p.merge_pre(slist=self.slist,
                                            n_candles=CONFIG.getint('pivots', 'n_candles'),
                                            diff_th=CONFIG.getint('pivots', 'diff_th'))
                            if CONFIG.getboolean('counter', 'runmerge_aft') is True and p.aft is not None:
                                p.merge_aft(slist=self.slist,
                                            n_candles=CONFIG.getint('pivots', 'n_candles'),
                                            diff_th=CONFIG.getint('pivots', 'diff_th'))
                            pl.append(p)

        return PivotList(plist=pl,
                         clist=self.clist,
                         slist=self.slist)

    def get_pl_bytime(self, adatetime):
        """
        Function that returns a new PivotList in which
        the plist is >= 'adatetime'

        Returns
        -------
        PivotList object
        """
        pl_logger.debug("Running get_pivots_lasttime")

        new_pl = []
        for p in self.plist:
            if p.candle['time'] >= adatetime:
                new_pl.append(p)

        new_PLobj = PivotList(plist=new_pl,
                              clist=self.clist,
                              slist=self.slist)

        pl_logger.debug("Done set_pivots_lasttime")

        return new_PLobj

    def plot_pivots(self, outfile_prices, outfile_rsi):
        '''
        Function to plot all pivots that are in the area

        Parameters
        ----------
        outfile_prices : filename
                         Output file for prices plot
        outfile_rsi : filename
                      Output file for rsi plot
        '''
        pl_logger.debug("Running plot_pivots")

        prices, rsi, datetimes = ([] for i in range(3))
        for c in self.clist.data['candles']:
            prices.append(c[CONFIG.get('general', 'part')])
            rsi.append(c['rsi'])
            datetimes.append(c['time'])

        # getting the fig size from settings
        figsize = literal_eval(CONFIG.get('images', 'size'))
        # massage datetimes so they can be plotted in X-axis
        x = [mdates.date2num(i) for i in datetimes]

        # plotting the rsi values
        fig_rsi = plt.figure(figsize=figsize)
        ax_rsi = plt.axes()
        ax_rsi.plot(datetimes, rsi, color="black")
        fig_rsi.savefig(outfile_rsi, format='png')

        # plotting the prices for part
        fig = plt.figure(figsize=figsize)
        ax = plt.axes()
        ax.plot(datetimes, prices, color="black")

        for p in self.plist:
            dt = p.candle['time']
            ix = datetimes.index(dt)
            # prepare the plot for 'pre' segment
            if p.pre is not None:
                ix_pre_s = datetimes.index(p.pre.start())
                plt.scatter(datetimes[ix_pre_s], prices[ix_pre_s], s=200, c='green', marker='v')
            # prepare the plot for 'aft' segment
            if p.aft is not None:
                ix_aft_e = datetimes.index(p.aft.end())
                plt.scatter(datetimes[ix_aft_e], prices[ix_aft_e], s=200, c='red', marker='v')
            # plot
            plt.scatter(datetimes[ix], prices[ix], s=50)

        fig.savefig(outfile_prices, format='png')

        pl_logger.debug("plot_pivots Done")

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key,
                                               value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
