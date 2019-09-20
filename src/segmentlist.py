from itertools import tee, islice, chain
from utils import *

import config
import numpy as np
import matplotlib.pyplot as plt

class SegmentList(object):
    '''
    Class that represents a list of segments

    Class variables
    ---------------
    slist : list, Required
            List of Segment objects
    instrument : str, Required
                 Pair

    '''

    def __init__(self, slist, instrument):

        # initialize the 'diff' attribute in each segment
        self.slist=[s.calc_diff() for s in slist]
        self.instrument = instrument

    def __trim_edge_segs(self, pip_th, candle_th):
        '''
        Private function to trim the edges of the 'slist'.
        By trimming I mean to remove the segments below 'pip_th' and 'candle_th'

        Parameters
        ----------
        pip_th: int
                Number of pips used as threshold to consolidate segments
                Required
        candle_th: int
                Number of candles used as threshold to consolidate segments
                Required

        Returns
        -------
        list with Segments with edge segments removed. It will also update the
        'self.slist' attribute segment list
        '''

        # removing elements at the beginning of the segment list
        nlist=self.slist
        for s in self.slist:
            if s.diff > pip_th or s.count > candle_th:
                break
            else:
                nlist=nlist[1:]

        # removing elements at the end of the segment list
        for s in reversed(nlist):
            if s.diff > pip_th or s.count > candle_th:
                break
            else:
                nlist.pop()

        self.slist=nlist

        return nlist

    def merge_segments(self, min_n_candles, diff_in_pips, outfile=None):
        '''
        Function to reduce segment complexity and
        to merge the minor trend to the major trend.
        For example:
        We have a segment like the following:
        1,1,1-1,-1,1,1. After running this function we
        will get 1,1,1,1,1,1,1

        Parameters
        ----------
        min_n_candles: int, Required
                       Minimum number of candles for this segment to be considered short
        diff_in_pips: int, Required
                      Minimum number of pips for this segment to be considered short
        outfile: File
                 Print the merged segments to thie .png file

        Returns
        -------
        It will return a list of SegmentLists. Each SegmentList will represent
        a merged segment. The list will be sorted from most recent segment
        to oldest
        '''

        y=[]
        dates=[]
        if outfile is not None:
            for s in self.slist:
                y=y+[getattr(x, config.CTDBT['part']) for x in s.clist]
                dates=dates+[getattr(x, 'time') for x in s.clist]

        # trim the edge segments for irrelevant segments
        nlist=self.__trim_edge_segs(pip_th=100,candle_th=10)

        pdb.set_trace()
        flistb=[] # list of SegmentLists
        flist=[] # list of lists, each sublist is a merged segment
        slist=[]
        pr_s=None
        is_first=False
        for s in reversed(nlist):
            if pr_s is None:
                pr_s=s
                slist.append(s)
                is_first = True
                continue
            else:
                if s.is_short(min_n_candles, diff_in_pips) is True:
                    is_first = False
                    slist.append(s)
                elif len(slist)==0 and s.is_short(min_n_candles, diff_in_pips) is False:
                    # segment is long but is the first one in a new major segment
                    slist.append(s)
                    is_first=True
                else:
                    # segment is long
                    if is_first is True:
                        flist.append(reversed(slist))
                        flistb.append(SegmentList(instrument=self.instrument,slist=reversed(slist)))
                        slist=[]
                        slist.append(s)
                    else:
                        slist.append(s)
                        flist.append(reversed(slist))
                        flistb.append(SegmentList(instrument=self.instrument, slist=reversed(slist)))
                        slist=[]

        if len(slist)>0:
            flist.append(reversed(slist))
            flistb.append(SegmentList(instrument=self.instrument, slist=reversed(slist)))

        pdb.set_trace()
        # the code below is just to plot the merged segments
        if outfile is not None:
            x = [*range(0, len(dates), 1)]
            xarr = np.array(x)
            yarr = np.array(y)
            ix_start=[]
            ix_end=[]
            for ms in reversed(flist):
                start=ms[-1].clist[0].time
                end=ms[0].clist[-1].time
                ix_start.append(np.where(dates == np.datetime64(start))[0][0])
                ix_end.append(np.where(dates == np.datetime64(end))[0][0])
            fig = plt.figure(figsize=config.PNGFILES['fig_sizes'])
            plt.plot(xarr, yarr, 'k:', alpha=0.5)
            plt.scatter(xarr[[ix_start]], yarr[[ix_start]], color='g')
            plt.scatter(xarr[[ix_end]], yarr[[ix_end]], color='r')
            fixs=[]
            for i, j in zip(ix_start, ix_end):
                fixs.append(i)
                fixs.append(j)
            plt.plot(xarr[[fixs]], yarr[[fixs]], 'k-')
            fig.savefig(outfile, format='png')

        return flistb

    def length(self):
        '''
        Get length in terms of number of candles representing the sum of candles in each Segment
        of the SegmentList

        Returns
        -------
        int
        '''

        length=0
        for s in self.slist:
            length=length+len(s.clist)

        return length

    def start(self):
        '''
        Get the start datetime for this SegmentList
        This start will be the time of the first candle in SegmentList

        Returns
        -------
        A datetime object
        '''

        return self.slist[0].clist[0].time

    def end(self):
        '''
        Get the end datetime for this SegmentList
        This start will be the time of the first candle in SegmentList

        Returns
        -------
        A datetime object
        '''

        return self.slist[-1].clist[-1].time


class Segment(object):
    '''
    Class containing a Segment object identified using the function 'get_segment_list' from the PivotList

    Class variables
    ---------------
    type : int, Required
           1 or -1
    count : int, Required
            Number of entities of 'type'
    clist : CandleList, Required
            CandleList with list of candles for this Segment
    instrument : str, Required
                 Pair
    diff : int, Optional
           Diff in number of pips between the first and the last candles in this segment
    '''

    def __init__(self, type, count, clist, instrument, diff=None):
        self.type = type
        self.count = count
        self.clist = clist
        self.instrument = instrument
        self.diff = diff

    def merge(self, s):
        '''
        Function to merge self to s. The merge will be done by
        concatenating s.clist to self.clist and increasing self.count to
        self.count+s.count

        Parameters
        ----------
        s : Segment object to be merge

        Returns
        -------
        Nothing
        '''

        self.clist=s.clist+self.clist
        self.count=len(self.clist)

    def calc_diff(self, part="openAsk"):
        '''
        Function to calculate the absolute difference in
        number of pips between the first and the last candles
        of this segment

        Parameters
        ---------
        part : What part of the candles used for calculating the difference.
               Default: 'openAsk'

        Returns
        -------
        It will set the 'diff' class member attribute
        '''

        # calculate the diff in pips between the last and first candles of this segment
        diff = abs(getattr(self.clist[-1],part) - getattr(self.clist[0],part))
        diff_pips = float(calculate_pips(self.instrument, diff))

        self.diff=diff_pips

        return self

    def is_short(self, min_n_candles, diff_in_pips):
        '''
        Function to check if segment is short (self.diff < pip_th or self.count < candle_th)

        Parameters
        ----------
        min_n_candles: int, Required
                       Minimum number of candles for this segment to be considered short
        diff_in_pips: int, Required
                      Minimum number of pips for this segment to be considered short

        Returns
        -------
        True if is short
        '''

        if self.count < min_n_candles  and self.diff < diff_in_pips:
            return True
        else:
            return False

    def length(self):
        '''
        Function to get the length of a segment

        Returns
        -------
        int Number of candles of this segment
        '''

        return len(self.clist)

    def __repr__(self):
        return "Segment"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str