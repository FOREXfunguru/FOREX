import logging
from utils import *
from zigzag import *
from segment import SegmentList
from segment import Segment
from candle.candle import Candle

# create logger
p_logger = logging.getLogger(__name__)
p_logger.setLevel(logging.INFO)

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
    """

    def __init__(self, type, candle, pre, aft,
                 score=None):
        self.type = type
        self.candle = candle
        self.pre = pre
        self.aft = aft
        self.score = score

    def merge_pre(self, slist, n_candles, diff_th):
        """
        Function to merge 'pre' Segment. It will merge self.pre with previous segment
        if self.pre and previous segment are of the same type (1 or -1) or count of
        previous segment is less than CONFIG.getint('pivots', 'n_candles')

        Parameters
        ----------
        slist : SegmentList object
                SegmentList for PivotList of this Pivot.
                Required
        n_candles : int
                    Skip merge if Segment is greater than 'n_candles'
        diff_th : int
                  % of diff in pips threshold

        Returns
        -------
        Nothing
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
                # s.count is less than CONFIG.getint('pivots', 'n_candles')
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
                # and s.count is greater than CONFIG.getint('pivots', 'n_candles')
                extension_needed = False

        p_logger.debug("self.pre start after-merge: {0}".format(self.pre.start()))
        p_logger.debug("Done merge_pre")

    def merge_aft(self, slist, n_candles, diff_th):
        """
        Function to merge 'aft' Segment. It will merge self.aft with next segment
        if self.aft and next segment are of the same type (1 or -1) or count of
        next segment is less than 'n_candles'

        Parameters
        ----------
        slist : SegmentList object
                SegmentList for PivotList of this Pivot.
                Required
        n_candles : int
                    Skip merge if Segment is greater than 'n_candles'
        diff_th : int
                  % of diff in pips threshold

        Returns
        -------
        Nothing
        """

        p_logger.debug("Running merge_aft")
        p_logger.debug("Analysis of pivot {0}".format(self.candle['time']))
        p_logger.debug("self.aft end before the merge: {0}".format(self.aft.end()))

        extension_needed = True
        while extension_needed is True:
            # increase end of self.aft by one candle
            start_dt = self.aft.end()+periodToDelta(1, self.candle['granularity'])

            # fetch next segment
            s = slist.fetch_by_start(start_dt)
            if s is None:
                # This is not necessarily an error, it could be that there is not the required Segment in slist
                # because it is out of the time period
                p_logger.info("No Segment could be retrieved for pivot falling in time {0} by using s.fetch_by_"
                              "start and date: {1} in function 'merge_aft'. ".format(self.candle.time, start_dt))
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
        The score will be the result of adding the number
        of candles of the 'pre' and 'aft' segments (if defined)

        Parameters
        ----------
        type : Type of score that will be
               calculated. Possible values: 'diff' , 'candles'
               Default: 'diff'

        Returns
        -------
        int  with the score of this pivot.
             It will also set the score class attribute
        """

        if self.pre:
            score_pre = 0
            if type == 'diff':
                score_pre = self.pre.diff
            elif type == 'candles':
                score_pre = len(self.pre.clist)
        else:
            score_pre = 0

        if self.aft:
            score_aft = 0
            if type == 'diff':
                score_aft = self.aft.diff
            elif type == 'candles':
                score_aft = len(self.aft.clist)
        else:
            score_aft = 0

        self.score = score_pre+score_aft

        return score_pre+score_aft

    def adjust_pivottime(self, clistO):
        '''
        Function to adjust the pivot time
        This is necessary as sometimes the Zigzag algorithm
        does not find the correct pivot

        Parameters
        ----------
        clistO : CandleList object used to identify the
                PivotList, Required
        Returns
        -------
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

        return datetime.strptime(new_pc.time, '%Y-%m-%dT%H:%M:%S.%fZ')

    def __repr__(self):
        return "Pivot"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str

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
            plist_o.append(Pivot(type=pre_i,
                                 candle=c_dict,
                                 pre=pre_s,
                                 aft=None))
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
            c_time = datetime.strptime(p.candle['time'],
                                       '%Y-%m-%dT%H:%M:%S.%fZ')
            if c_time == d:
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

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key,
                                               value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
