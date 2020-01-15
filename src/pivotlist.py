import pdb
from zigzag import *
from segmentlist import *
from utils import *
import warnings

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

    def __init__(self, clist, parray=None, plist=None, slist=None):

        self.clist = clist

        if parray is not None:
            # pivots_to_modes function from the Zigzag indicator
            modes = pivots_to_modes(parray)
            segs = [] # this list will hold the Segment objects
            plist_o = [] # this list will hold the Pivot objects
            pre_s=None # Variable that will hold pre Segments
            ix=0
            start_ix=None
            end_ix=None
            pre_i=None
            ix=0
            for i in parray:
                if (i==1 or i==-1) and start_ix is None:
                    # First pivot
                    start_ix=ix
                    pre_i=i
                elif (i==1 or i==-1) and start_ix is not None:
                    end_ix=ix
                    if parray[start_ix+1]==0:
                        submode=modes[start_ix+1:end_ix]
                    else:
                        submode=[modes[start_ix+1]]
                    #checking if all elements in submode are the same:
                    assert len(np.unique(submode).tolist())==1, "more than one type in modes"
                    # create Segment
                    s = Segment(type=submode[0],
                                count=end_ix-start_ix,
                                clist=clist.clist[start_ix:end_ix],
                                instrument=clist.instrument)
                    # create Pivot object
                    pobj = Pivot(type=pre_i, candle=clist.clist[start_ix], pre=pre_s, aft=s)
                    # Append it to list
                    plist_o.append(pobj)
                    # Append it to segs
                    segs.append(s)
                    start_ix=ix
                    pre_s=s
                    pre_i=i
                ix+=1
            # add last Pivot
            plist_o.append(Pivot(type=pre_i, candle=clist.clist[start_ix], pre=pre_s, aft=None))
            self.plist = plist_o
            self.slist = SegmentList(slist=segs, instrument=plist_o[0].candle.instrument)
        else:
            self.plist = plist
            self.slist = slist

    def fetch_by_time(self, d):
        '''
        Function to fetch a Pivot object using a
        datetime

        Returns
        -------
        Pivot object
              None if not Pivot found
        '''

        for p in self.plist:
            if p.candle.time==d:
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

        pl=[]

        for p in self.plist:
            if p.type==type:
                pl.append(p)

        return PivotList(plist=pl,clist=self.clist, slist=self.slist)


class Pivot(object):
    '''
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
    '''

    def __init__(self, type, candle, pre, aft, score=None):
        self.type = type
        self.candle = candle
        self.pre = pre
        self.aft = aft
        self.score =score

    def merge_pre(self, slist, n_candles):
        '''
        Function to merge 'pre' Segment. It will merge self.pre with previous segment
        if self.pre and previous segment are of the same type (1 or -1) or count of
        previous segment is less than 'n_candles'

        Parameters
        ----------
        slist : SegmentList object
                SegmentList for PivotList of this Pivot.
                Required
        n_candles : int
                    Skip merge if Segment is less than 'n_candles'.
                    Required

        Returns
        -------
        Nothing
        '''

        pro=0 #variable that will hold the diff in pips in favour of trend
        anti=0 #variable that will hold the diff in pips against the trend

        extension_needed = True
        while extension_needed is True:
            # reduce start of self.pre by one candle
            start_dt = self.pre.start() - periodToDelta(1, self.candle.granularity)

            # fetch previous segment
            s = slist.fetch_by_end(start_dt)
            if s is None:
                warnings.warn("No Segment could be retrieved for pivot falling in time {0} "
                              "by using s.fetch_by_end and date: {1} in function 'merge_pre'".format(self.candle.time,
                                                                                                     start_dt))
                extension_needed=False
                continue
            if self.type==1:
                if s.type==1:
                    pro+=s.diff
                elif s.type==-1:
                    anti+=s.diff

            if self.pre.type == s.type:
                # merge
                self.pre = self.pre.prepend(s)
            elif self.pre.type != s.type and s.count < n_candles:
                # merge
                self.pre = self.pre.prepend(s)
            else:
                extension_needed = False

    def merge_aft(self, slist, n_candles):
        '''
        Function to merge 'aft' Segment. It will merge self.aft with next segment
        if self.aft and next segment are of the same type (1 or -1) or count of
        next segment is less than 'n_candles'

        Parameters
        ----------
        slist : SegmentList object
                SegmentList for PivotList of this Pivot.
                Required
        n_candles : int
                    Skip merge if Segment is less than 'n_candles'.
                    Required

        Returns
        -------
        Nothing
        '''

        extension_needed=True
        while extension_needed is True:
            # increase end of self.aft by one candle§
            start_dt=self.aft.end()+periodToDelta(1, self.candle.granularity)

            # fetch next segment
            s=slist.fetch_by_start(start_dt)
            if s is None:
                warnings.warn("No Segment could be retrieved for pivot falling in time {0} by using s.fetch_by_"
                              "start and date: {1} in function 'merge_aft'. ".format(self.candle.time, start_dt))
                extension_needed = False
                continue

            if self.aft.type == s.type:
                # merge
                self.aft=self.aft.append(s)
            elif self.aft.type != s.type and s.count<n_candles:
                # merge
                self.aft=self.aft.append(s)
            else:
                extension_needed = False

    def calc_score(self):
        '''
        Function to calculate the score for this Pivot
        The score will be the result of adding the number
        of candles of the 'pre' and 'aft' segment (if defined)

        Returns
        -------
        int Score and it will set the score class attribute
        '''
        if self.pre :
            score_pre=len(self.pre.clist)
        else:
            score_pre=0
        if self.aft:
            score_aft=len(self.aft.clist)
        else:
            score_aft=0

        self.score=score_pre+score_aft

        return score_pre+score_aft

    def __repr__(self):
        return "Pivot"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str