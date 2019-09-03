from itertools import tee, islice, chain
from utils import *

import config

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

    def __previous_and_next(self, some_iterable):
        prevs, items, nexts = tee(some_iterable, 3)
        prevs = chain([None], prevs)
        nexts = chain(islice(nexts, 1, None), [None])
        return zip(prevs, items, nexts)

    def merge_segments(self):
        '''
        Function to reduce segment complexity and
        to merge the minor trend to the major trend.
        For example:
        We have a segment like the following:
        1,1,1-1,-1,1,1. After running this function we
        will get 1,1,1,1,1,1,1

        Parameters
        ----------

        Returns
        -------
        It will set the self.slist class member to the reduced Segment list
        '''

        pdb.set_trace()

        # trim the edge segments for irrelevant segments
        nlist=self.__trim_edge_segs(pip_th=100,candle_th=10)

        flist=[] # list of lists, each sublist is a merged segment
        slist=[]
        pr_s=None
        is_first=False
        for s in reversed(nlist):
            if pr_s is None:
                pr_s=s
                slist.append(s)
                continue
            else:
                if s.is_short() is True:
                    slist.append(s)
                elif len(slist)==0 and s.is_short() is False:
                    # segment is long but is the first one in a new major segment
                    slist.append(s)
                    is_first=True
                else:
                    # segment is long
                    if is_first is True:
                        flist.append(slist)
                        is_first=False
                        slist=[]
                        slist.append(s)
                    else:
                        slist.append(s)
                        flist.append(slist)
                        slist=[]

        print("h")





        """
        merged=False
        nslist=[]
        in_count=0
        ix=0
        pdb.set_trace()
        previous=None
        item=None
        for previous, item, nxt in self.__previous_and_next(reversed(nlist)):
            item=item
            if ix==0:
                ix += 1
                continue
            elif merged is True:
                in_count+=1
                if in_count==2:
                    if item.diff < pip_th and item.count < candle_th:
                        if (previous.diff > pip_th or previous.count > candle_th) \
                                and (nxt.diff > pip_th or nxt.count > candle_th):
                            merged = True
                            nslist[-1].merge(item)
                            nslist[-1].merge(nxt)
                            previous = nslist[-1]
                            in_count=0
                        elif (previous.diff > pip_th or previous.count > candle_th) \
                                and (nxt.diff < pip_th and nxt.count < candle_th):
                            merged=True
                            nslist[-1].merge(item)
                            previous=nslist[-1]
                            in_count-=1
                    else:
                        merged=False
                continue
            else:
                if item.diff < pip_th and item.count < candle_th:
                    if (previous.diff > pip_th or previous.count > candle_th) \
                        and (nxt.diff > pip_th or nxt.count > candle_th):
                        merged=True
                        previous.merge(item)
                        previous.merge(nxt)
                        nslist.append(previous)
                        previous=previous
                        print("h")
                else:
                    if previous.diff > pip_th or previous.count > candle_th:
                        nslist.append(previous)
                        previous=previous
            ix+=1
        nslist.append(item)
        """

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

    def is_short(self):
        '''
        Function to check if segment is short (self.diff < pip_th or self.count < candle_th)

        Returns
        -------
        True if is short
        '''

        if self.count < config.SEGMENT['min_n_candles']  and self.diff < config.SEGMENT['diff_in_pips']:
            return True
        else:
            return False

    def __repr__(self):
        return "Segment"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str