import pdb
from zigzag import *
from segmentlist import *
from utils import *

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
            pr_ix=0 # record the ix of 1st candle in segment
            count = 0 # record how many candles of a certain type
            type = None # record previous type
            for i in modes:
                if type is None:
                    type = i
                    count += 1
                    ix += 1
                    continue
                else:
                    if i == type:
                        count += 1
                    else:
                        # create Segment
                        s = Segment(type=type,
                                    count=count,
                                    clist=clist.clist[pr_ix:ix],
                                    instrument=clist.instrument)
                        # create Pivot object
                        pobj=Pivot(type=type, candle=clist.clist[pr_ix], pre=pre_s, aft=s)
                        # Append it to list
                        plist_o.append(pobj)
                        type = i # type has changed
                        count = 1
                        segs.append(s)
                        pr_ix = ix # new ix for 1st candle
                        pre_s=s # new s for previous Segment
                ix += 1

            #add last Segment
            ls=Segment(type=type,
                       count=count,
                       clist=clist.clist[pr_ix:ix],
                     instrument=clist.instrument)
            segs.append(ls)
            #add last Pivot
            plist_o.append(Pivot(type=type,candle=clist.clist[pr_ix], pre=pre_s, aft=ls))
            self.plist=plist_o
            self.slist = SegmentList(slist=segs, instrument=plist_o[0].candle.instrument)
        else:
            self.plist=plist
            self.slist=slist


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
        cl=[]
        sl=[]
        for (p, c, s) in zip(self.plist, self.clist.clist, self.slist.slist):
            if p.type==type:
                pl.append(p)
                cl.append(c)
                sl.append(s)

        return PivotList(plist=pl,clist=cl, slist=sl)


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
    '''

    def __init__(self, type, candle, pre, aft):
        self.type = type
        self.candle = candle
        self.pre = pre
        self.aft = aft

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

        extension_needed = True
        while extension_needed is True:
            # reduce start of self.pre by one candle
            start_dt = self.pre.start() - periodToDelta(1, self.candle.granularity)

            # fetch previous segment
            s = slist.fetch_by_end(start_dt)

            if self.pre.type == s.type:
                # merge
                self.pre = self.pre.merge(s)
            elif self.pre.type != s.type and s.count < n_candles:
                # merge
                self.pre = self.pre.merge(s)
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
            # increase end of self.aft by one candle
            start_dt=self.aft.end()+periodToDelta(1, self.candle.granularity)

            # fetch next segment
            s=slist.fetch_by_start(start_dt)

            if self.aft.type == s.type:
                # merge
                self.aft=self.aft.append(s)
            elif self.aft.type != s.type and s.count<n_candles:
                # merge
                self.aft=self.aft.append(s)
            else:
                extension_needed = False


    def __repr__(self):
        return "Pivot"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str