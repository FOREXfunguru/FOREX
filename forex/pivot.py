import logging
from utils import *
from forex.candle.candle import Candle
from forex.params import pivots_params
# create logger
p_logger = logging.getLogger(__name__)
p_logger.setLevel(logging.INFO)

class Pivot(object):
    """
    Class representing a single Pivot

    Class variables
    ---------------
    type : Type of pivot. It can be 1 or -1
    candle : Candle object ovrerlapping this pivot
    pre : Segment object
          Segment object before this pivot
    aft : Segment object
          Segment object after this pivot
    score : iResult of adding the number
            of candles of the 'pre' and 'aft' segment (if defined). Optional
    """
    def __init__(self, type: int, candle, pre, aft,
                 score: int=None):
        self.type = type
        self.candle = candle
        self.pre = pre
        self.aft = aft
        self.score = score

    def merge_pre(self, slist, n_candles: int, diff_th: int)->None:
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
        p_logger.debug("Analysis of pivot {0}".format(self.candle['time']))
        p_logger.debug("self.pre start pre-merge: {0}".format(self.pre.start()))

        extension_needed = True # if extension_needed is False then no further attempts of extending this self.pre
                                # will be tried
        while extension_needed is True:
            # reduce start of self.pre by one candle in order to retrieve the previous segment
            # by its end
            start_dt = self.pre.start() - periodToDelta(1, self.candle['granularity'])

            # fetch previous segment
            s = None
            if pivots_params.max_diff:
                s = slist.fetch_by_end(start_dt, max_diff=0)
            else:
                s = slist.fetch_by_end(start_dt)

            if s is None:
                # This is not necessarily an error, it could be that there is not the required Segment in slist
                # because it is out of the time period
                p_logger.info("No Segment could be retrieved for pivot falling in time {0} "
                              "by using s.fetch_by_end and date: {1} in function 'merge_pre'".format(self.candle['time'],
                                                                                                     start_dt))
                extension_needed = False
                continue
            if self.pre.type == s.type:
                # merge if type of previous (s) is equal to self.pre
                p_logger.debug("Merge because of same Segment type")
                self.pre = self.pre.prepend(s)
            elif self.pre.type != s.type and s.count < n_candles:
                # merge if types of previous (s) and self.pre are different but
                # s.count is less than pivots_params.n_candles
                # calculate the % that s.diff is with respect to self.pre.diff
                perc_diff = s.diff*100/self.pre.diff
                # do not merge if perc_diff that s represents with respect
                # to s.pre is > than the defined threshold
                if perc_diff < diff_th:
                    p_logger.debug("Merge because of s.count < n_candles")
                    self.pre = self.pre.prepend(s)
                else:
                    p_logger.debug("Skipping merge because of %_diff")
                    extension_needed = False
            else:
                # exit the while loop, as type of previous (s) and self.pre are different
                # and s.count is greater than pivots_params.n_candles
                extension_needed = False

        p_logger.debug("self.pre start after-merge: {0}".format(self.pre.start()))
        p_logger.debug("Done merge_pre")

    def merge_aft(self, slist, n_candles: int, diff_th: int)->None:
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
        p_logger.debug("Analysis of pivot {0}".format(self.candle['time']))
        p_logger.debug("self.aft end before the merge: {0}".format(self.aft.end()))

        extension_needed = True
        while extension_needed is True:
            # increase end of self.aft by one candle
            start_dt = self.aft.end()+periodToDelta(1, self.candle['granularity'])

            # fetch next segment
            s = None
            if pivots_params.max_diff:
                s = slist.fetch_by_start(start_dt, max_diff=0)
            else:
                s = slist.fetch_by_start(start_dt)
            if s is None:
                # This is not necessarily an error, it could be that there is not the required Segment in slist
                # because it is out of the time period
                p_logger.info("No Segment could be retrieved for pivot falling in time {0} by using s.fetch_by_"
                              "start and date: {1} in function 'merge_aft'. ".format(self.candle['time'], start_dt))
                extension_needed = False
                continue

            if self.aft.type == s.type:
                p_logger.debug("Merge because of same Segment type")
                # merge
                self.aft = self.aft.append(s)
            elif self.aft.type != s.type and s.count < n_candles:
                # calculate the % that s.diff is with respect to self.pre.diff
                perc_diff = s.diff * 100 / self.aft.diff
                # do not merge if perc_diff that s represents with respect
                # to s.aft is > than the defined threshold
                if perc_diff < diff_th:
                    p_logger.debug("Merge because of s.count < n_candles")
                    self.aft = self.aft.append(s)
                else:
                    p_logger.debug("Skipping merge because of %_diff")
                    extension_needed = False
            else:
                extension_needed = False

        p_logger.debug("self.aft end after-merge: {0}".format(self.aft.end()))
        p_logger.debug("Done merge_aft")

    def calc_score(self, type='diff'):
        """
        Function to calculate the score for this Pivot
        The score will be the result of adding the 'diff'
        values or adding the number of candles of the 'pre' and 'aft'
        segments (if defined)

        Arguments:
            type : Type of score that will be
                   calculated. Possible values: 'diff' , 'candles'

        Returns:
            int /float with the score of this pivot.
            It will also set the score class attribute
        """
        if self.pre:
            score_pre = 0
            if type == 'diff':
                score_pre = self.pre.diff
            elif type == 'candles':
                score_pre = self.pre.count
        else:
            score_pre = 0

        if self.aft:
            score_aft = 0
            if type == 'diff':
                score_aft = self.aft.diff
            elif type == 'candles':
                score_aft = self.aft.count
        else:
            score_aft = 0

        self.score = score_pre+score_aft

        return score_pre+score_aft

    def adjust_pivottime(self, clistO):
        '''Function to adjust the pivot time
        This is necessary as sometimes the Zigzag algorithm
        does not find the correct pivot

        Arguments:
            clistO : CandleList object used to identify the
                    PivotListt
        Returns:
            New adjusted datetime
        '''
        clist = clistO.data['candles'][:-1] # reduce index by 1 so start candle+1 is not included
        new_pc = pre_colour = None
        it = True
        ix = -1
        while it is True:
            c_dict = clist[ix]
            c = Candle(dict_data=c_dict)
            c.set_candle_features()
            if c.colour == "undefined":
                it = False
                new_pc = c
                continue
            if pre_colour is None:
                pre_colour = c.colour
                ix -= 1
            elif c.colour == pre_colour:
                ix -= 1
                continue
            else:
                # change in candle colour
                new_pc = c
                it = False
        return new_pc.time

    def __repr__(self):
        return "Pivot"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str