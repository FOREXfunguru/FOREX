from utils import *
from configparser import ConfigParser

class Segment(object):
    '''
    Class containing a Segment object identified linking the pivots in a the PivotList

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
    settingf : str, Optional
               Path to *.ini file with settings
    settings : ConfigParser object generated using 'settingf'
    '''

    def __init__(self, type, count, clist, instrument,
                 settingf=None, settings=None, diff=None):
        self.type = type
        self.count = count
        self.clist = clist
        self.instrument = instrument
        self.diff = diff
        self.settingf = settingf

        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

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

        part = self.settings.get('general', 'part')

        # calculate the diff in pips between the last and first candles of this segment
        diff = abs(getattr(self.clist[-1], part) - getattr(self.clist[0], part))
        diff_pips = float(calculate_pips(self.instrument, diff))

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
