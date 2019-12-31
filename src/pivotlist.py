import pdb
from zigzag import *
from segmentlist import *

class PivotList(object):
    '''
    Class that represents a list of Pivots as identified
    by the Zigzag indicator

    Class variables
    ---------------
    plist : list, Required
            List of pivots obtained using the 'peak_valley_pivots' function from Zigzag indicator
    slist : SegmentList object, Derived
            List of Segment objects connecting the pivot points. For obtaining these segments
            I use the function 'pivots_to_modes' implemented in the Zigzag indicator
    mslist : List of SegmentList objects, each of the SegmentList object will be merged (obtained
             by running the function 'segmentlist.merge_segments()', Derived
    clist : CandleList object
            CandleList for this PivotList
    '''

    def __init__(self, plist, clist):
        self.clist = clist

        # pivots_to_modes function from the Zigzag indicator
        modes = pivots_to_modes(plist)

        segs = [] # this list will hold the Segment objects
        plist_o = [] # this list will hold the Pivot objects
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
                    pdb.set_trace()
                    # create Pivot and append it to list
                    plist_o.append(Pivot(type=type,candle=clist.clist[pr_ix]))
                    type = i # type has changed
                    count = 1
                    segs.append(s)
                    pr_ix = ix # new ix for 1st candle
            ix += 1

        #add last Segment
        segs.append(Segment(type=type,
                            count=count,
                            clist=clist.clist[pr_ix:ix],
                            instrument=clist.instrument))
        #add last Pivot
        plist_o.append(Pivot(type=type,candle=clist.clist[pr_ix]))

        self.slist=SegmentList(slist=segs, instrument=clist.instrument)

        #initialize merged Segment Lists
        self.mslist = self.slist.merge_segments(outfile="testAft.png", min_n_candles=20,
                                                diff_in_pips=20000)

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
    '''

    def __init__(self, type, candle):
        self.type = type
        self.candle = candle

    def __repr__(self):
        return "Pivot"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str