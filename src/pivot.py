import warnings
from utils import *
from configparser import ConfigParser


class Pivot(object):
    """
    Class that represents a single Pivot as identified
    by the Zigzag indicator

    Class variables
    ---------------
    type : int, Required
           Type of pivot. It can be 1 or -1
    candle : Candle Object
             Candle representing the pivot
    pre : Segment object
          Segment object before this pivot
    aft : Segment object
          Segment object after this pivot
    score : int
            Result of adding the number
            of candles of the 'pre' and 'aft' segment (if defined). Optional
    settingf : str, Optional
               Path to *.ini file with settings
    settings : ConfigParser object generated using 'settingf'
    """

    def __init__(self, type, candle, pre, aft,
                 settingf=None, settings=None,
                 score=None):
        self.type = type
        self.candle = candle
        self.pre = pre
        self.aft = aft
        self.score = score

        self.settingf = settingf

        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

    def merge_pre(self, slist):
        """
        Function to merge 'pre' Segment. It will merge self.pre with previous segment
        if self.pre and previous segment are of the same type (1 or -1) or count of
        previous segment is less than self.settings.getint('pivots', 'n_candles')

        Parameters
        ----------
        slist : SegmentList object
                SegmentList for PivotList of this Pivot.
                Required

        Returns
        -------
        Nothing
        """

        extension_needed = True # if extension_needed is False then no further attempts of extending this self.pre
                                # will be tried
        while extension_needed is True:
            # reduce start of self.pre by one candle in order to retrieve the previous segment
            # by its end
            start_dt = self.pre.start() - periodToDelta(1, self.candle.granularity)

            # fetch previous segment
            s = slist.fetch_by_end(start_dt)
            if s is None:
                warnings.warn("No Segment could be retrieved for pivot falling in time {0} "
                              "by using s.fetch_by_end and date: {1} in function 'merge_pre'".format(self.candle.time,
                                                                                                     start_dt))
                extension_needed = False
                continue

            if self.pre.type == s.type:
                # merge if type of previous (s) is equal to self.pre
                self.pre = self.pre.prepend(s)
            elif self.pre.type != s.type and s.count < self.settings.getint('pivots', 'n_candles'):
                # merge if types of previous (s) and self.pre are different but
                # s.count is less than self.settings.getint('pivots', 'n_candles')
                pdb.set_trace()
                (self.pre.diff
                 s.diff
                self.pre = self.pre.prepend(s)
            else:
                # exit the while loop, as type of previous (s) and self.pre are different
                # and s.count is greater than self.settings.getint('pivots', 'n_candles')
                extension_needed = False

    def merge_aft(self, slist):
        """
        Function to merge 'aft' Segment. It will merge self.aft with next segment
        if self.aft and next segment are of the same type (1 or -1) or count of
        next segment is less than 'n_candles'

        Parameters
        ----------
        slist : SegmentList object
                SegmentList for PivotList of this Pivot.
                Required

        Returns
        -------
        Nothing
        """

        extension_needed = True
        while extension_needed is True:
            # increase end of self.aft by one candle§
            start_dt = self.aft.end()+periodToDelta(1, self.candle.granularity)

            # fetch next segment
            s = slist.fetch_by_start(start_dt)
            if s is None:
                warnings.warn("No Segment could be retrieved for pivot falling in time {0} by using s.fetch_by_"
                              "start and date: {1} in function 'merge_aft'. ".format(self.candle.time, start_dt))
                extension_needed = False
                continue

            if self.aft.type == s.type:
                # merge
                self.aft = self.aft.append(s)
            elif self.aft.type != s.type and s.count < self.settings.getint('pivots', 'n_candles'):
                # merge
                self.aft = self.aft.append(s)
            else:
                extension_needed = False

    def calc_score(self):
        """
        Function to calculate the score for this Pivot
        The score will be the result of adding the number
        of candles of the 'pre' and 'aft' segments (if defined)

        Returns
        -------
        int  with the score of this pivot.
             It will also set the score class attribute
        """
        if self.pre :
            score_pre = len(self.pre.clist)
        else:
            score_pre = 0
        if self.aft:
            score_aft = len(self.aft.clist)
        else:
            score_aft = 0

        self.score = score_pre+score_aft

        return score_pre+score_aft

    def __repr__(self):
        return "Pivot"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str