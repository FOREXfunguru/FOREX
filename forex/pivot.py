import logging
import datetime
import matplotlib.pyplot as plt

from utils import periodToDelta, substract_pips2price, add_pips2price
from params import gparams, pivots_params
from forex.segment import SegmentList, Segment
from zigzag import *
from statistics import mean

# create logger
p_logger = logging.getLogger(__name__)
p_logger.setLevel(logging.INFO)


class Pivot(object):
    """
    Class representing a single Pivot

    Class variables:
        type : Type of pivot. It can be 1 or -1
        candle : Candle object ovrerlapping this pivot
        pre : Segment object before this pivot. When type=-1, pre.type will
              be 1. When type=1, pre.type will be -1
        aft : Segment object after this pivot. When type=-1, aft.type will
              be -1. When type=1, aft.type will be 1
        score : Result of adding the number
                of candles of the 'pre' and 'aft' segment (if defined)
    """
    def __init__(self, type: int, candle, pre, aft,
                 score: int = None):
        self.type = type
        self.candle = candle
        self.pre = pre
        self.aft = aft
        self.score = score

    def merge_pre(self, slist, n_candles: int, diff_th: int) -> None:
        """Function to merge 'pre' Segment. It will merge self.pre with previous segment
        if self.pre and previous segment are of the same type (1 or -1) or count of
        previous segment is less than pivots_params.n_candles

        Arguments:
            slist : SegmentList object
                    SegmentList for PivotList of this Pivot.
            n_candles : Skip merge if Segment is greater than 'n_candles'
            diff_th : % of diff in pips threshold
        """
        p_logger.debug("Running merge_pre")
        p_logger.debug("Analysis of pivot {0}".format(self.candle.time))
        p_logger.debug("self.pre start pre-merge: {0}".format(self.pre.start()))

        extension_needed = True
        while extension_needed is True:
            # reduce start of self.pre by one candle in order to retrieve the previous segment
            # by its end
            start_dt = self.pre.start() - periodToDelta(1, self.candle.granularity)

            s = slist.fetch_by_end(start_dt)
            if s is None:
                # This is not necessarily an error, it could be that there is not the required Segment in slist
                # because it is out of the time period
                p_logger.info("No Segment could be retrieved for pivot falling in time {0} "
                              "by using s.fetch_by_end and date: {1} in function 'merge_pre'".format(self.candle.time,
                                                                                                     start_dt))
                extension_needed = False
                continue
            if self.pre.type == s.type:
                # merge if type of previous (s) is equal to self.pre
                p_logger.debug("Merge because of same Segment type")
                self.pre.prepend(s)
            elif self.pre.type != s.type and len(s.clist) < n_candles:
                # merge if types of previous segment and self.pre are
                # different but len(s.clist) is less than n_candles
                # calculate the % that s.diff is with respect to self.pre.diff
                perc_diff = s.diff*100/self.pre.diff
                # do not merge if perc_diff that s represents with respect
                # to s.pre is > than the defined threshold
                if perc_diff < diff_th:
                    p_logger.debug("Merge because of len(s.clist) < n_candles")
                    self.pre.prepend(s)
                else:
                    p_logger.debug("Skipping merge because of %_diff")
                    extension_needed = False
            else:
                # exit the while loop, as type of previous (s) and self.pre are different
                # and s.count is greater than n_candles
                extension_needed = False

        p_logger.debug("self.pre start after-merge: {0}".format(self.pre.start()))
        p_logger.debug("Done merge_pre")

    def merge_aft(self, slist, n_candles: int, diff_th: int) -> None:
        """Function to merge 'aft' Segment. It will merge self.aft with next segment
        if self.aft and next segment are of the same type (1 or -1) or count of
        next segment is less than 'n_candles'

        Arguments:
            slist : SegmentList object
                    SegmentList for PivotList of this Pivot.
            n_candles : Skip merge if Segment is greater than 'n_candles'
            diff_th : % of diff in pips threshold
        """
        p_logger.debug("Running merge_aft")
        p_logger.debug("Analysis of pivot {0}".format(self.candle.time))
        p_logger.debug("self.aft end before the merge: {0}".format(self.aft.end()))

        extension_needed = True
        while extension_needed is True:
            # increase end of self.aft by one candle
            start_dt = self.aft.end()+periodToDelta(1,
                                                    self.candle.granularity)

            # fetch next segment
            s = slist.fetch_by_start(start_dt)
            if s is None:
                # This is not necessarily an error, it could be that there is
                # not the required Segment in slist
                # because it is out of the time period
                p_logger.info(f"No Segment could be retrieved for pivot falling in" 
                              f"time {self.candle.time} by using s.fetch_by_"
                              f"start and date: {start_dt} in function 'merge_aft'")
                extension_needed = False
                continue
            if self.aft.type == s.type:
                p_logger.debug("Merge because of same Segment type")
                self.aft.append(s)
            elif self.aft.type != s.type and len(s.clist) < n_candles:
                # calculate the % that s.diff is with respect to self.pre.diff
                perc_diff = s.diff * 100 / self.aft.diff
                # do not merge if perc_diff that s represents with respect
                # to s.aft is > than the defined threshold
                if perc_diff < diff_th:
                    p_logger.debug("Merge because of len(s.clist) < n_candles")
                    self.aft.append(s)
                else:
                    p_logger.debug("Skipping merge because of %_diff")
                    extension_needed = False
            else:
                extension_needed = False

        p_logger.debug("self.aft end after-merge: {0}".format(self.aft.end()))
        p_logger.debug("Done merge_aft")

    def calc_score(self, type='diff') -> float:
        """
        Function to calculate the score for this Pivot
        The score will be the result of adding the 'diff'
        values or adding the number of candles of the 'pre' and 'aft'
        segments (if defined)

        Arguments:
            type : Type of score that will be
                   calculated. Possible values: 'diff' , 'candles'
        """
        if self.pre:
            score_pre = 0
            if type == 'diff':
                score_pre = self.pre.diff
            elif type == 'candles':
                score_pre = len(self.pre.clist)
        else:
            score_pre = 0.0

        if self.aft:
            score_aft = 0
            if type == 'diff':
                score_aft = self.aft.diff
            elif type == 'candles':
                score_aft = len(self.aft.clist)
        else:
            score_aft = 0.0

        return round(score_pre+score_aft, 2)

    def adjust_pivottime(self, clistO):
        """Function to adjust the pivot time
        This is necessary as sometimes the Zigzag algorithm
        does not find the correct pivot.

        Arguments:
            clistO : CandleList object used to identify the
                     PivotList
        Returns:
            New adjusted datetime
        """
        clist = clistO.candles # reduce index by 1 so start candle+1
                               # is not included
        new_pc, pre_colour = None, None
        it = True
        ix = -1
        while it is True:
            cObj = clist[ix]
            if cObj.colour == "undefined":
                it = False
                new_pc = cObj
                continue
            if pre_colour is None:
                if cObj.colour == 'green' and self.type == -1:
                    new_pc = cObj
                    it = False
                elif cObj.colour == 'red' and self.type == 1:
                    new_pc = cObj
                    it = False
                pre_colour = cObj.colour
                ix -= 1
            elif self.type == -1:
                if cObj.colour == 'red' and cObj.colour == pre_colour:
                    ix -= 1
                    continue
                else:
                    new_pc = cObj
                    it = False
            elif self.type == 1:
                if cObj.colour == 'green' and cObj.colour == pre_colour:
                    ix -= 1
                    continue
                else:
                    new_pc = cObj
                    it = False
        return new_pc.time

    def __repr__(self):
        return "Pivot"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str


class PivotList(object):
    """Class that represents a list of Pivots as identified
    by the Zigzag indicator.

    Class variables:
        clist: CandleList object
        pivots: List with Pivot objects
        slist: SegmentList object"""

    def __init__(self, clist, pivots=None, slist=None,
                 th_bounces: float = None) -> None:
        self.clist = clist
        if pivots is not None:
            assert slist is not None, "Error!. SegmentList needs to be provided"
            self.slist = slist
            self.pivots = pivots
        else:
            if th_bounces:
                po_l, segs = self._get_pivotlist(th_bounces)
            else:
                po_l, segs = self._get_pivotlist(pivots_params.th_bounces)
            self.pivots = po_l
            self.slist = SegmentList(slist=segs,
                                     instrument=clist.instrument)

    def __iter__(self):
        self.pos = 0
        return self

    def __next__(self):
        if (self.pos < len(self.pivots)):
            self.pos += 1
            return self.pivots[self.pos - 1]
        else:
            raise StopIteration
 
    def __getitem__(self, key):
        return self.pivots[key]
 
    def __len__(self):
        return len(self.pivots)

    def _get_pivotlist(self, th_bounces: float):
        """Function to obtain a pivotlist object containing pivots identified
        using the Zigzag indicator.

        Arguments:
            th_bounces: Value used by ZigZag to identify pivots. The lower the
                        value the higher the sensitivity

        Returns:
            List with Pivot objects
            List with Segment objects
        """
        yarr = np.array([cl.c for cl in self.clist.candles])
        pivots = peak_valley_pivots(yarr, th_bounces,
                                    th_bounces*-1)
        modes = pivots_to_modes(pivots)

        segs = []  # this list will hold the Segment objects
        plist_o = []  # this list will hold the Pivot objects
        pre_s = None # Variable that will hold pre Segments
        ixs = list(np.where(np.logical_or(pivots == 1, pivots == -1))[0])
        tuples_lst = [(ixs[i], ixs[i+1]) for i in range(len(ixs)-1)]
        for pair in tuples_lst:
            if pivots[pair[0]+1] == 0:
                submode = modes[pair[0]+1:pair[1]]
            else:
                submode = [modes[pair[0]+1]]
            #checking if all elements in submode are the same:
            assert len(np.unique(submode).tolist()) == 1, "more than one type in modes"
            s = Segment(type=submode[0],
                        clist=self.clist.candles[pair[0]:pair[1]],
                        instrument=self.clist.instrument)
            # create Pivot object
            cl = self.clist.candles[pair[0]]
            # add granularity to object
            cl.granularity = self.clist.granularity
            pobj = Pivot(type=submode[0],
                         candle=cl,
                         pre=pre_s, 
                         aft=s)
            pobj.score = pobj.calc_score()
            # Append it to list
            plist_o.append(pobj)
            # Append it to segs
            segs.append(s)
            pre_s = s
        
        # add last Pivot
        cl = self.clist.candles[ixs[-1]]
        cl.granularity = self.clist.granularity
        l_pivot = Pivot(type=modes[ixs[-1]],
                        candle=cl,
                        pre=pre_s,
                        aft=None)
        l_pivot.score = l_pivot.calc_score()
        plist_o.append(l_pivot)
        return plist_o, segs

    def fetch_by_time(self, d: datetime) -> Pivot:
        '''Function to fetch a Pivot object using a datetime'''
        p = next((p for p in self.pivots if p.candle.time == d), None)
        return p

    def fetch_by_type(self, type: int) -> 'PivotList':
        '''Function to get all pivots from a certain type.

        Arguments:
            type : 1 or -1
        '''

        pl = [p for p in self.pivots if p.type == type]

        return PivotList(pivots=pl,
                         clist=self.clist,
                         slist=self.slist)

    def print_pivots_dates(self) -> list:
        '''Function to generate a list with the datetimes of the different
          Pivots in PivotList'''

        datelist = []
        for p in self.pivots:
            datelist.append(p.candle.time)

        return datelist

    def get_score(self) -> float:
        '''Function to calculate the score after adding the score
        for each individual pivot'''

        tot_score = sum(p.score for p in self.pivots)
        return round(tot_score, 1)

    def get_avg_score(self) -> float:
        '''Function to calculate the avg score
        for all pivots in this PivotList.
        This calculation is done by dividing the
        total score by the number of pivots
        '''
        avg = mean(p.score for p in self.pivots)
        return round(avg, 1)

    def inarea_pivots(self, price: float, last_pivot: bool = True):
        '''
        Function to identify the candles for which price is in the area defined
        by SR+HRpips and SR-HRpips

        Arguments:
            pivots: PivotList object
            SR: price of the S/R area
            last_pivot: If True, then the last pivot will be considered as it is part
                        of the setup. Default: True

        Returns:
            PivotList with the pivots that are in the area centered at 'price'
        '''
        # get bounces in the horizontal SR area
        lower = substract_pips2price(self.clist.instrument,
                                     price,
                                     pivots_params.hr_pips)
        upper = add_pips2price(self.clist.instrument,
                               price,
                               pivots_params.hr_pips)

        p_logger.debug("SR U-limit: {0}; L-limit: {1}".format(round(upper, 4),
                                                              round(lower, 4)))

        pl = []
        for p in self.pivots:
            # always consider the last pivot in bounces.plist as in_area as
            # this part of the entry setup
            if self.pivots[-1].candle.time == p.candle.time and last_pivot is True:
                adj_t = p.adjust_pivottime(clistO=self.clist)
                newclist = self.clist.slice(start=self.clist.candles[0].time,
                                            end=adj_t)
                newpl = PivotList(clist=newclist)
                newp = newpl._get_pivotlist(pivots_params.th_bounces)[0][-1]
                if pivots_params.runmerge_pre is True and newp.pre is not None:
                    newp.merge_pre(slist=self.slist,
                                   n_candles=pivots_params.n_candles,
                                   diff_th=pivots_params.diff_th)
                if pivots_params.runmerge_aft is True and newp.aft is not None:
                    newp.merge_aft(slist=self.slist,
                                   n_candles=pivots_params.n_candles,
                                   diff_th=pivots_params.diff_th)
                pl.append(newp)
            else:
                part_list = ['c']
                if p.type == 1:
                    part_list.append('h')
                elif p.type == -1:
                    part_list.append('l')

                for part in part_list:
                    price = getattr(p.candle, part)
                    # only consider pivots in the area
                    if price >= lower and price <= upper:
                        # check if this pivot already exists in pl
                        p_seen = False
                        for op in pl:
                            if op.candle.time == p.candle.time:
                                p_seen = True
                        if p_seen is False:
                            p_logger.debug(f"Pivot {p.candle.time} identified in area")
                            if pivots_params.runmerge_pre is True and p.pre is not None:
                                p.merge_pre(slist=self.slist,
                                            n_candles=pivots_params.n_candles,
                                            diff_th=pivots_params.diff_th)
                            if pivots_params.runmerge_aft is True and p.aft is not None:
                                p.merge_aft(slist=self.slist,
                                            n_candles=pivots_params.n_candles,
                                            diff_th=pivots_params.diff_th)
                            pl.append(p)

        return PivotList(clist=self.clist,
                         pivots=pl,
                         slist=self.slist)

    def calc_itrend(self):
        '''Function to calculate the datetime for the start of this CandleList,
        assuming that this CandleList is trending. This function will calculate
          the start of the trend by using the self.get_pivots function

        Returns:
            Merged Segment object containing the trend_i
        '''
        p_logger.debug("Running calc_itrend")
        for p in reversed(self.pivots):
            adj_t = p.adjust_pivottime(clistO=self.clist)
            start = self.pivots[0].candle.time
            newclist = self.clist.slice(start= start,
                                        end=adj_t)
            newp = PivotList(clist=newclist).pivots[-1]
            newp.merge_pre(slist=self.slist,
                           n_candles=pivots_params.n_candles,
                           diff_th=pivots_params.diff_th)
            return newp.pre

        p_logger.debug("Done clac_itrend")

    def plot_pivots(self, outfile_prices: str, outfile_rsi: str):
        '''Function to plot all pivots that are in the area

        Arguments:
            outfile_prices : Output file for prices plot.
            outfile_rsi : Output file for rsi plot.
        '''
        p_logger.debug("Running plot_pivots")

        prices, rsi, datetimes = ([] for i in range(3))
        for c in self.clist.candles:
            prices.append(c.c)
            rsi.append(c.rsi)
            datetimes.append(c.time)

        # plotting the rsi values
        fig_rsi = plt.figure(figsize=gparams.size)
        ax_rsi = plt.axes()
        ax_rsi.plot(datetimes, rsi, color="black")
        fig_rsi.savefig(outfile_rsi, format='png')

        # plotting the prices for part
        fig = plt.figure(figsize=gparams.size)
        ax = plt.axes()
        ax.plot(datetimes, prices, color="black")

        for p in self.pivots:
            dt = p.candle.time
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

        p_logger.debug("plot_pivots Done")

    def pivots_report(self, outfile: str) -> str:
        """Function to generate a report of the pivots in the PivotList

        Arguments:
            outfile : Path to file with report

        Returns:
            file with PivotList report with Pivots information.
             This file will have the following format:
             #pre.start|p.candle.time|p.aft.end
        """
        f = open(outfile, 'w')
        f.write("#pre.start|p.candle['time']|p.aft.end\n")
        for p in self.pivots:
            if p.pre is None and p.aft is not None:
                f.write("{0}|{1}|{2}\n".format("n.a.", p.candle.time, p.aft.end()))
            elif p.pre is not None and p.aft is not None:
                f.write("{0}|{1}|{2}\n".format(p.pre.start(), p.candle.time, p.aft.end()))
            elif p.pre is not None and p.aft is None:
                f.write("{0}|{1}|{2}\n".format(p.pre.start(), p.candle.time, "n.a."))
        f.close

        return outfile

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key,
                                               value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
