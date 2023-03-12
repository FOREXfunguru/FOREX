import matplotlib
import datetime
import pickle
import pdb

from forex.candle import Candle
from utils import *

matplotlib.use('PS')

class Segment(object):
    """Class containing a Segment object identified linking the pivots in a the PivotList

    Class variables
    ---------------
    type : 1 or -1
    clist : List of dictionaries, in which each of the dicts is a candle
    instrument : Pair"""

    def __init__(self, type: int, clist: list, instrument: str):
        self.type = type
        self.clist = clist
        self.instrument = instrument
        self._diff = self._calc_diff()

    @property
    def diff(self):
        return self._diff
    
    def pickle_dump(self, outfile: str)->str:
        '''Function to pickle this particular Segment
        
        Arguments:
            outfile: Path used to pickle
            
        Returns:
            path to file with pickled data
        '''
        
        pickle_out = open(outfile,"wb")
        pickle.dump(self, pickle_out)
        pickle_out.close()

        return outfile

    @classmethod
    def pickle_load(self, infile: str):
        '''Function to pickle this particular Segment
        
        Arguments:
            infile: Path used to load in pickled data
            
        Returns:
            inseg: Segment object    
        '''
        pickle_in = open(infile,"rb")
        inseg = pickle.load(pickle_in)

        return inseg

    def prepend(self, s)->None:
        '''Function to prepend s to self. The merge will be done by
        concatenating s.clist to self.clist and increasing self.count to
        self.count+s.count

        Arguments:
            s : Segment object to be merged
        '''

        self.clist = s.clist+self.clist
        self._diff = self._calc_diff()

    def append(self, s)->None:
        '''Function to append s to self. The merge will be done by
        concatenating self.clist to self.clist and increasing self.count to
        self.count+s.count

        Arguments:
            s : Segment object to be merged        
        '''
        self.clist = self.clist+s.clist
        self._diff = self._calc_diff()

    def _calc_diff(self)->float:
        '''Private function to calculate the absolute difference in
        number of pips between the first and the last candles
        of this segment. The candle part considered is
        controlled by gparams.part
        '''
        diff = abs(float(self.clist[-1][1]['c'])- float(self.clist[0][1]['c']))
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

    def start(self)->datetime:
        '''Function that returns the start of this Segment'''
        return try_parsing_date(self.clist[0][0])

    def end(self)->datetime:
        '''Function that returns the end of this Segment'''        
        return try_parsing_date(self.clist[-1][0])

    def get_lowest(self)->Candle:
        '''Function to get the candle with the lowest price in self.clist

        Returns:
            Candle object
        '''
        sel_c = price = None
        for c in self.clist:
            if price is None:
                price = float(c[1]['l'])
                sel_c = c
            elif float(c[1]['l']) < price:
                price = float(c[1]['l'])
                sel_c = c
        c_dict= sel_c[1]
        c_dict['time'] = sel_c[0]
        cl = Candle(**c_dict)
        return cl

    def get_highest(self)->Candle:
        '''Function to get the candle with the highest price in self.clist

        Returns:
            Candle object
        '''
        price = sel_c = None
        for c in self.clist:
            if price is None:
                price = float(c[1]['h'])
                sel_c = c
            elif float(c[1]['h']) > price:
                price = float(c[1]['h'])
                sel_c = c
        c_dict= sel_c[1]
        c_dict['time'] = sel_c[0]
        cl = Candle(**c_dict)
        return cl

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
    
    @property
    def diff(self):
        return self._diff
    
    def __iter__(self):
        self.pos = 0
        return self
 
    def __next__(self):
        if(self.pos < len(self.slist)):
            self.pos += 1
            return self.slist[self.pos - 1]
        else:
            raise StopIteration
    
    def __getitem__(self, key):
        return self.slist[key]
    
    def __len__(self):
        return len(self.slist)
    
    def pickle_dump(self, outfile: str)->str:
        '''Function to pickle this particular SegmentList
        
        Arguments:
            outfile: Path used to pickle
            
        Returns:
            path to file with pickled data
        '''
        
        pickle_out = open(outfile,"wb")
        pickle.dump(self, pickle_out)
        pickle_out.close()

        return outfile

    @classmethod
    def pickle_load(self, infile: str):
        '''Function to pickle this particular SegmentList
        
        Arguments:
            infile: Path used to load in pickled data
            
        Returns:
            inseg: Segment object    
        '''
        pickle_in = open(infile,"rb")
        inseglst = pickle.load(pickle_in)

        return inseglst

    def calc_diff(self)->float:
        '''Function to calculate the difference in terms
        of number of pips between the 1st candle in
        the 1st segment and the last candle in the
        last segment

        Returns:
            float representing the diff in pips. It will be positive
            when it is a downtrend and negative otherwise
        '''
        diff = float(self.slist[0].clist[0][1]['c']) - float(self.slist[-1].clist[-1][1]['c'])
        diff_pips = float(calculate_pips(self.instrument, diff))

        if diff_pips == 0:
            diff_pips += 1.0

        self._diff = diff_pips

    def length_cl(self)->int:
        '''Get length in terms of number of candles representing the sum of candles in each Segment
        of the SegmentList'''

        length=0
        for s in self.slist:
            length = length+len(s.clist)
        return length

    def start(self)->datetime:
        '''Get the start datetime for this SegmentList
        This start will be the time of the first candle in SegmentList'''
        return try_parsing_date(self.slist[0].clist[0][0])

    def end(self)->datetime:
        '''Get the end datetime for this SegmentList
        This start will be the time of the first candle in SegmentList'''
        return try_parsing_date(self.slist[-1].clist[-1][0])

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
            dt_st = s.start()
            if s.start() == dt or dt_st > dt or abs(dt_st-dt) <= timedelta(0, max_diff):
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
            dt_end =  s.end()
            if dt_end == dt or dt_end < dt or dt_end-dt <= timedelta(0, max_diff):
                return s

    def __repr__(self):
        return "SegmentList"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str
