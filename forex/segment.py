from utils import *
import matplotlib
import datetime
from forex.params import gparams

matplotlib.use('PS')

class Segment(object):
    """Class containing a Segment object identified linking the pivots in a the PivotList

    Class variables
    ---------------
    type : 1 or -1
    count : Number of candles
    clist : List of dictionaries, in which each of the dicts is a candle
    instrument : Pair"""

    def __init__(self, type: int, count: int, clist: list, instrument: str):
        self.type = type
        self.count = count
        self.clist = clist
        self.instrument = instrument
        self._diff = self._calc_diff()

    @property
    def diff(self):
        return self._diff

    def prepend(self, s):
        '''Function to prepend s to self. The merge will be done by
        concatenating s.clist to self.clist and increasing self.count to
        self.count+s.count

        Arguments:
            s : Segment object to be merged
        '''

        self.clist = s.clist+self.clist
        self.count = len(self.clist)
        self._calc_diff()

    def append(self, s):
        '''Function to append s to self. The merge will be done by
        concatenating self.clist to self.clist and increasing self.count to
        self.count+s.count

        Returns:
            self
        '''
        self.clist = self.clist+s.clist
        self.count = len(self.clist)
        self.calc_diff()

    def _calc_diff(self)->float:
        '''Private function to calculate the absolute difference in
        number of pips between the first and the last candles
        of this segment. The candle part considered is
        controlled by gparams.part
        '''
        diff = abs(self.clist[-1].c - self.clist[0].c)
        diff_pips = float(calculate_pips(self.instrument, diff))
        if diff_pips ==0:
            diff_pips = 1.0 
        return diff_pips

    def is_short(self, min_n_candles: int, diff_in_pips: int)->bool:
        '''Function to check if segment is short (self.diff < pip_th or self.count < candle_th)

        Arguments:
            min_n_candles: Minimum number of candles for this segment to be considered short
            diff_in_pips: Minimum number of pips for this segment to be considered short

        Returns:
            True if is short
        '''

        if self.count < min_n_candles and self.diff < diff_in_pips:
            return True
        else:
            return False

    def length(self)->int:
        '''Function to get the length of a segment

        Returns:
            Number of candles of this segment
        '''
        return len(self.clist)

    def start(self)->datetime:
        '''Function that returns the start of this Segment'''
        return self.clist[0]['time']

    def end(self)->datetime:
        '''Function that returns the end of this Segment'''
        return self.clist[-1]['time']

    def get_lowest(self):
        '''Function to get the lowest candle (i.e., the candle with the lowest lo
        candle.lowAsk) price in self.clist

        Returns:
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
        '''Function to get the highest candle (i.e., the candle with the highest lo
        candle.highAsk) price in self.clist

        Returns:
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
    '''Class that represents a list of segments

    Class variables
    ---------------
    slist : List of Segment objects
    instrument : Pair
    diff : Diff in pips between first candle in first Segment
           and last candle in the last Segment
    '''

    def __init__(self, slist: list, instrument: str):
        self.slist = slist
        self.instrument = instrument
        self._diff = self.calc_diff() 

    def calc_diff(self)->float:
        '''Function to calculate the difference in terms
        of number of pips between the 1st candle in
        the 1st segment and the last candle in the
        last segment

        Returns:
            float representing the diff in pips. It will be positive
            when it is a downtrend and negative otherwise
        '''
        diff = self.slist[0].clist[0].c - self.slist[-1].clist[-1].c
        diff_pips = float(calculate_pips(self.instrument, diff))

        if diff_pips == 0:
            diff_pips += 1.0
        self.diff = diff_pips

    def length(self)->int:
        '''Get length in terms of number of candles representing the sum of candles in each Segment
        of the SegmentList'''

        length=0
        for s in self.slist:
            length = length+len(s.clist)

        self.length = length

        return length

    def start(self)->datetime:
        '''Get the start datetime for this SegmentList
        This start will be the time of the first candle in SegmentList'''
        self.start = self.slist[0].clist[0]['time']

        return self.start

    def end(self)->datetime:
        '''Get the end datetime for this SegmentList
        This start will be the time of the first candle in SegmentList'''

        self.end = self.slist[-1].clist[-1]['time']

        return self.end

    def fetch_by_start(self, dt: datetime, max_diff: int=3600):
        '''Function to get a certain Segment by
        the start Datetime

        Arguments:
            dt: Start of segment datetime used
                for fetching the Segment
            max_diff : Max discrepancy in number of seconds for the difference dt-s.start()
                       Default: 3600 secs (i.e. 1hr). This is relevant when analysing
                       with granularity = H1 or lower.

        Returns:
            Segment object. None if not found
        '''
        for s in self.slist:
            if s.start() == dt or s.start() > dt or abs(s.start()-dt) <= datetime.timedelta(0, max_diff):
                return s

        return None

    def fetch_by_end(self, dt: datetime, max_diff: int=3600):
        '''Function to get a certain Segment by
        the end Datetime

        Arguments:
            dt: End of segment datetime used
                for fetching the Segment
            max_diff : Max discrepancy in number of seconds for the difference dt-s.end()
                       Default: 3600 secs (i.e. 1hr). This is relevant when analysing
                       with granularity = H1 or lower.

        Returns:
            Segment object. None if not found'''

        for s in reversed(self.slist):
            if s.end() == dt or s.end() < dt or s.end()-dt <= datetime.timedelta(0, max_diff):
                return s

    def __repr__(self):
        return "SegmentList"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str
