from utils import *

import config
import numpy as np
import matplotlib
matplotlib.use('PS')
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
    diff : int, Optional
           Diff in pips between first candle in first Segment
           and last candle in the last Segment

    '''

    def __init__(self, slist, instrument):

        # initialize the 'diff' attribute in each segment
        self.slist=[s.calc_diff() for s in slist]
        self.instrument = instrument
        self.diff=self.calc_diff()

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

    def calc_diff(self, part="openAsk"):
        '''
        Function to calculate the difference in terms
        of number of pips betweeen the 1st candle in
        the 1st segment and the last candle in the
        last segment

        Parameters
        ---------
        part : What part of the candles used for calculating the difference.
               Default: 'openAsk'

        Returns
        -------
        float representing the diff in pips. It will be positive
        when it is a downtrend and negative otherwise
        '''

        diff = (getattr(self.slist[0].clist[0], part) -
                getattr(self.slist[-1].clist[-1], part))
        diff_pips = float(calculate_pips(self.instrument, diff))

        self.diff=diff_pips

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
                       Minimum number of candles for this segment not to be considered retracement
        diff_in_pips: int, Required
                      Minimum number of pips for this segment not to be considered retracement
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

        flist=[] # final list of SegmentLists
        slist=[]
        pr_s=None
        is_first=False

        for s in nlist:
            if pr_s is None:
                # Initialize all structures
                pr_s=s
                slist.append(s)
                is_first = True
                continue
            else: # structures have been initialized
                if s.is_short(min_n_candles, diff_in_pips) is True:
                    is_first = False
                    slist.append(s)
                elif len(slist)==0 and s.is_short(min_n_candles, diff_in_pips) is False:
                    # segment is long but is the first one in a new non short segment
                    slist.append(s)
                    is_first=True
                elif pr_s.is_short(min_n_candles, diff_in_pips) is True:
                    # previous segment is short so merge the current to the previous one
                    slist.append(s)
                    pr_s=s
                else:
                    # current segment is long and the previous one is non-short
                    if is_first is True:
                        #append to final structure the previous slist
                        flist.append(SegmentList(instrument=self.instrument,slist=slist))
                        slist=[] # reinitialize list
                        slist.append(s) # add first segment
                    else:
                        # is_first is False, this means that previous Segment is short
                        slist.append(s)
                        flist.append(SegmentList(instrument=self.instrument, slist=slist))
                        slist=[]

        if len(slist)>0:
            if slist[0].is_short(min_n_candles, diff_in_pips) is True:
                # first segment in 'slist' is short, so merge this slist to flist
                nlist=flist[-1].slist
                nlist.extend(slist)
                nslist=SegmentList(instrument=self.instrument, slist=nlist)
                flist[-1]=nslist
            else:
                flist.append(SegmentList(instrument=self.instrument, slist=slist))

        # check the direction of SegmentLists in order to see if there 2 consecutive
        # SegmentLists with the same direction. If that's the case then merge the two
        # SegmentLists
        [x.calc_diff() for x in flist]
        prev_sign=None
        flistb=[]
        for slist in flist:
        #    print("{0}-{1}:{2}".format(slist.start(),slist.end(),slist.diff))
            if prev_sign is None:
                if slist.diff>0:
                    prev_sign='-'
                else:
                    prev_sign='+'
                flistb.append(slist)
            else:
                merge=False
                if slist.diff>0 and prev_sign is '-':
                    #merge segments because they have the same sign
                    merge=True
                elif slist.diff<0 and prev_sign is '+':
                    # merge segments because they have the same sign
                    merge = True
                else:
                    if slist.diff>0:
                        prev_sign='-'
                    else:
                        prev_sign = '+'
                if merge is True:
                    nlist = flistb[-1].slist
                    nlist.extend(slist.slist)
                    nslist = SegmentList(instrument=self.instrument, slist=nlist)
                    flistb[-1] = nslist
                    if slist.diff > 0:
                        prev_sign = '-'
                    else:
                        prev_sign = '+'
                else:
                    flistb.append(slist)
        # the code below is just to plot the merged segments
        if outfile is not None:
            x = [*range(0, len(dates), 1)]
            xarr = np.array(x) # convert to numpy array
            yarr = np.array(y) # convert to numpy array
            ix_start=[]
            ix_end=[]
            # iterate over each of the SegmentLists representing
            # each merged segment
            for ms in flistb:
                ix_start.append(np.where(dates == np.datetime64(ms.start()))[0][0]) # get the ix in dates of the start of merged
                                                                                    # segment
                ix_end.append(np.where(dates == np.datetime64(ms.end()))[0][0]) # get the ix in dates of the end of merged
                                                                                # segment
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

        self.length=length

        return length

    def start(self):
        '''
        Get the start datetime for this SegmentList
        This start will be the time of the first candle in SegmentList

        Returns
        -------
        A datetime object
        '''

        start=self.slist[0].clist[0].time
        self.start= start

        return start

    def end(self):
        '''
        Get the end datetime for this SegmentList
        This start will be the time of the first candle in SegmentList

        Returns
        -------
        A datetime object
        '''

        end= self.slist[-1].clist[-1].time
        self.end= end

        return end

    def fetch_by_start(self, dt):
        '''
        Function to get a certain Segment by
        the start Datetime

        Parameters
        ----------
        dt: Datetime
            Start of segment datetime used
            for fetching the Segment

        Returns
        -------
        Segment object. None if not found
        '''

        for s in self.slist:
            if s.start()==dt:
                return s

        return None


    def fetch_by_end(self, dt):
        '''
        Function to get a certain Segment by
        the end Datetime

        Parameters
        ----------
        dt: Datetime
            End of segment datetime used
            for fetching the Segment

        Returns
        -------
        Segment object. None if not found
        '''

        for s in self.slist:
            if s.end()==dt:
                return s

        return None


    def __repr__(self):
        return "SegmentList"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str


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
        self
        '''

        self.clist=s.clist+self.clist
        self.count=len(self.clist)

        return self

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

        if self.count < min_n_candles and self.diff < diff_in_pips:
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

    def start(self):
        '''
        Function that returns the start of this
        Segment

        Returns
        -------
        datetime
        '''
        return self.clist[0].time

    def end(self):
        '''
        Function that returns the end of this
        Segment

        Returns
        -------
        datetime
        '''
        return self.clist[-1].time


    def __repr__(self):
        return "Segment"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str
