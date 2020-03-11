from utils import *
import config
import numpy as np
import matplotlib
import datetime
matplotlib.use('PS')
import matplotlib.pyplot as plt
from configparser import ConfigParser


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
    settingf : str, Optional
               Path to *.ini file with settings
    settings : ConfigParser object generated using 'settingf'
    '''

    def __init__(self, slist, instrument, settingf=None, settings=None):

        self.settingf = settingf

        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

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
        part = self.settings.get('general', 'part')

        diff = (getattr(self.slist[0].clist[0], part) -
                getattr(self.slist[-1].clist[-1], part))
        diff_pips = float(calculate_pips(self.instrument, diff))

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

        start = self.slist[0].clist[0].time
        self.start = start

        return start

    def end(self):
        '''
        Get the end datetime for this SegmentList
        This start will be the time of the first candle in SegmentList

        Returns
        -------
        A datetime object
        '''

        end = self.slist[-1].clist[-1].time
        self.end = end

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
            if s.start() == dt or s.start() > dt:
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
