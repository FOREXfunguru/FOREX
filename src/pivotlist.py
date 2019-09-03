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
            Lisf of Segment objects connecting the pivot points. For obtaining these segments
            I use the function 'pivots_to_modes' implemented in the Zigzag indicator
    clist : CandleList object
            CandleList for this PivotList
    '''

    def __init__(self, plist, clist):
        self.plist = plist

        # initializing the slist class member
        modes = pivots_to_modes(plist)

        segs = []
        ix=0
        pr_ix=0
        count = 0
        type = None
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
                    s = Segment(type=type,
                                count=count,
                                clist=clist.clist[pr_ix:ix],
                                instrument=clist.instrument)
                    type = i
                    count = 1
                    segs.append(s)
                    pr_ix = ix
            ix += 1

        self.clist = clist
        segs.append(Segment(type=type,
                            count=count,
                            clist=clist.clist[pr_ix:ix],
                            instrument=clist.instrument))

        self.slist=SegmentList(slist=segs, instrument=clist.instrument)
