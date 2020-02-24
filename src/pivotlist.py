import pdb
from zigzag import *
from segmentlist import *
from pivot import Pivot
from segment import Segment
from configparser import ConfigParser
import traceback

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
    settingf : str, Optional
               Path to *.ini file with settings
    settings : ConfigParser object generated using 'settingf'
    '''

    def __init__(self, clist, parray=None, plist=None,
                 slist=None, settingf=None, settings=None):

        self.clist = clist
        self.settingf = settingf

        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

        if parray is not None:
            # pivots_to_modes function from the Zigzag indicator
            modes = pivots_to_modes(parray)
            segs = [] # this list will hold the Segment objects
            plist_o = [] # this list will hold the Pivot objects
            pre_s = None # Variable that will hold pre Segments
            ix = 0
            start_ix = None
            end_ix = None
            pre_i = None
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
                                clist=clist.clist[start_ix:end_ix],
                                instrument=clist.instrument,
                                settingf=self.settingf)
                    # create Pivot object
                    pobj = Pivot(type=pre_i,
                                 candle=clist.clist[start_ix],
                                 pre=pre_s,
                                 aft=s,
                                 settingf=self.settingf)
                    # Append it to list
                    plist_o.append(pobj)
                    # Append it to segs
                    segs.append(s)
                    start_ix = ix
                    pre_s = s
                    pre_i = i
                ix += 1
            # add last Pivot
            plist_o.append(Pivot(type=pre_i,
                                 candle=clist.clist[start_ix],
                                 pre=pre_s,
                                 aft=None,
                                 settingf=self.settingf))
            self.plist = plist_o
            self.slist = SegmentList(slist=segs,
                                     instrument=plist_o[0].candle.instrument,
                                     settingf=self.settingf)
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
            if p.candle.time == d:
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
            if p.type == type:
                pl.append(p)

        return PivotList(plist=pl,
                         clist=self.clist,
                         slist=self.slist,
                         settingf=self.settingf)

