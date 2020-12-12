from utils import *
from config import CONFIG
import matplotlib
import datetime
matplotlib.use('PS')

class Segment(object):
    '''
    Class containing a Segment object identified linking the pivots in a the PivotList

    Class variables
    ---------------
    type : int, Required
           1 or -1
    count : int, Required
            Number of entities of 'type'
    clist : List, Required
            List of dictionaries, in which each of the dicts is a candle
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

    def prepend(self, s):
        '''
        Function to prepend s to self. The merge will be done by
        concatenating s.clist to self.clist and increasing self.count to
        self.count+s.count

        Parameters
        ----------
        s : Segment object to be merge

        Returns
        -------
        self
        '''

        self.clist = s.clist+self.clist
        self.count = len(self.clist)

        return self

    def append(self, s):
        '''
        Function to append s to self. The merge will be done by
        concatenating self.clist to self.clist and increasing self.count to
        self.count+s.count

        Returns
        -------
        self
        '''

        self.clist = self.clist+s.clist
        self.count = len(self.clist)

        return self

    def calc_diff(self):
        '''
        Function to calculate the absolute difference in
        number of pips between the first and the last candles
        of this segment

        Returns
        -------
        It will set the 'diff' class member attribute
        '''

        part = CONFIG.get('general', 'part')
        # calculate the diff in pips between the last and first candles of this segment
        diff = abs(self.clist[-1][part] - self.clist[0][part])
        diff_pips = float(calculate_pips(self.instrument, diff))

        if diff_pips == 0:
            diff_pips += 1

        self.diff = diff_pips
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
        return self.clist[0]['time']

    def end(self):
        '''
        Function that returns the end of this
        Segment

        Returns
        -------
        datetime
        '''
        return self.clist[-1]['time']


    def get_lowest(self):
        '''
        Function to get the lowest candle (i.e., the candle with the lowest lo
        candle.lowAsk) price in self.clist

        Returns
        -------
        Candle object
        '''

        sel_c = price = None
        for c in self.clist:
            if price is None:
                price = c['lowAsk']
                sel_c = c
            elif c['lowAsk'] < price:
                price = c['lowAsk']
                sel_c = c

        return sel_c

    def get_highest(self):
        '''
        Function to get the highest candle (i.e., the candle with the highest lo
        candle.highAsk) price in self.clist

        Returns
        -------
        Candle object
        '''

        price = sel_c = None
        for c in self.clist:
            if price is None:
                price = c['highAsk']
                sel_c = c
            elif c['lowAsk'] > price:
                price = c['highAsk']
                sel_c = c

        return sel_c

    def __repr__(self):
        return "Segment"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str

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
        self.slist = [s.calc_diff() for s in slist]
        self.instrument = instrument
        self.diff = self.calc_diff()

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
        nlist = self.slist
        for s in self.slist:
            if s.diff > pip_th or s.count > candle_th:
                break
            else:
                nlist = nlist[1:]

        # removing elements at the end of the segment list
        for s in reversed(nlist):
            if s.diff > pip_th or s.count > candle_th:
                break
            else:
                nlist.pop()

        self.slist = nlist

        return nlist

    def calc_diff(self):
        '''
        Function to calculate the difference in terms
        of number of pips between the 1st candle in
        the 1st segment and the last candle in the
        last segment

        Returns
        -------
        float representing the diff in pips. It will be positive
        when it is a downtrend and negative otherwise
        '''
        part = CONFIG.get('general', 'part')

        diff = self.slist[0].clist[0][part] - self.slist[-1].clist[-1][part]
        diff_pips = float(calculate_pips(self.instrument, diff))

        if diff_pips == 0:
            diff_pips += 1
        self.diff = diff_pips

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
            length = length+len(s.clist)

        self.length = length

        return length

    def start(self):
        '''
        Get the start datetime for this SegmentList
        This start will be the time of the first candle in SegmentList

        Returns
        -------
        A datetime object
        '''
        self.start = self.slist[0].clist[0]['time']

        return self.start

    def end(self):
        '''
        Get the end datetime for this SegmentList
        This start will be the time of the first candle in SegmentList

        Returns
        -------
        A datetime object
        '''

        self.end = self.slist[-1].clist[-1]['time']

        return self.end

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
            if s.start() == dt or s.start() > dt or abs(s.start()-dt) <= datetime.timedelta(0, 3600):
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

        for s in reversed(self.slist):
            if s.end() == dt or s.end() < dt or s.end()-dt <= datetime.timedelta(0, 3600):
                return s

        return None

    def __repr__(self):
        return "SegmentList"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str
