from zigzag import *
#from forex.pivot_list import PivotList
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import pandas as pd
import numpy as np
import matplotlib
import datetime
import logging
from utils import *
from typing import List
from forex.candle.candle import Candle

from forex.params import gparams, pivots_params, clist_params

matplotlib.use('PS')
import matplotlib.pyplot as plt                                                                                                                                                        

logging.basicConfig(level=logging.INFO)

# create logger
cl_logger = logging.getLogger(__name__)
cl_logger.setLevel(logging.INFO)

class CandleList(object):
    """Class containing a list of Candles

    Class variables
    ---------------
    instrument : i.e. 'AUD_USD'
    granularity : i.e. 'D'
    candles : List of Candle objects
    type : Type of this CandleList. Possible values are 'long'/'short'"""
    def __init__(self, instrument: str, granularity: str, data: list):
        """Constructor

        Arguments:
            data: list of Dictionaries, each dict containing data for a Candle
        """
        self.candles = [Candle(**d) for d in data]
        self.instrument = instrument
        self.granularity = granularity
        self._type = self._guess_type()

    @property
    def type(self):
        return self._type
    
    def __iter__(self):
        self.pos = 0
        return self
 
    def __next__(self):
        if(self.pos < len(self.candles)):
            self.pos += 1
            return self.candles[self.pos - 1]
        else:
            raise StopIteration
    
    def __getitem__(self, key):
        return self.candles[key]
    
    def __len__(self):
        return len(self.candles)
    
    def _guess_type(self)->str:
        price_1st = self.candles[0].c
        price_last = self.candles[-1].c
        if price_1st > price_last:
            return 'short'
        elif price_1st < price_last:
            return 'long'

    def fetch_by_time(self, adatetime : datetime, period: int=0):
        '''Function to get a candle using its datetime

        Arguments:
            adatetime: datetime object for candle that wants
                       to be fetched
            period: Number of candles above/below 'adatetime' that will be fetched

        Returns:
            Candle object
        '''

        d=adatetime
        delta = None
        delta_period = None

        if self.data['granularity'] == "D":
            delta = timedelta(hours=24)
            delta_period = timedelta(hours=24*period)
        else:
            fgran = self.data['granularity'].replace('H', '')
            delta = timedelta(hours=int(fgran))
            delta_period = timedelta(hours=int(fgran)*period)

        if period == 0:
            sel_c = None
            for c in self.data['candles']:
                start = c['time']
                end = start+delta
                if d >= start and d < end:
                    sel_c = c

            if sel_c is None:
                raise Exception("No candle was selected with time: {0}\n."
                                " It is good to check if the marked is closed".format(datetime))
            return sel_c
        elif period > 0:
            start = d-delta_period
            end = d+delta_period
            sel_c = []
            for c in self.data['candles']:
                if c['time'] >= start and c['time'] <= end:
                    sel_c.append(c)
            if len(sel_c) == 0: raise Exception("No candle was selected"
                                                " for range: {0}-{1}".format(start, end))
            return sel_c

    def calc_rsi(self):
        '''Calculate the RSI for a certain candle list.'''
        cl_logger.debug("Running calc_rsi")

        start_time = self.data['candles'][0]['time']
        end_time = self.data['candles'][-1]['time']

        delta_period = None
        if self.data['granularity'] == "D":
            delta_period = timedelta(hours=24 * clist_params.period)
        else:
            fgran = self.data['granularity'].replace('H', '')
            delta_period = timedelta(hours=int(fgran) * clist_params.period)

        start_calc_time = start_time - delta_period

        #fetch candles from start_calc_time
        conn = Connect(instrument=self.data['instrument'],
                       granularity=self.data['granularity'])
        '''
        Get candlelist from start_calc_time to (start_time-1)
        This 2-step API call is necessary in order to avoid
        maximum number of candles errors
        '''
        ser_dir = None
        if hasattr(gparams, 'ser_data_dir'):
            ser_dir = gparams.set_data_dir

        cl_logger.debug("Fetching data from API")
        cl1_res = conn.query(start=start_calc_time.isoformat(),
                             end=start_time.isoformat(),
                             indir=ser_dir)

        '''Get candlelist from start_time to end_time'''
        cl2_res = conn.query(start=start_time.isoformat(),
                             end=end_time.isoformat(),
                             indir=ser_dir)

        if cl1_res['candles'][-1]['time'] == cl2_res['candles'][0]['time']:
            del cl1_res['candles'][-1]

        candle_list = cl1_res['candles'] + cl2_res['candles']
        series = [float(c['mid']['c']) for c in candle_list]

        df = pd.DataFrame({'close': series})
        chg = df['close'].diff(1)

        gain = chg.mask(chg < 0, 0)
        loss = chg.mask(chg > 0, 0)

        rsi_period = clist_params.rsi_period
        avg_gain = gain.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
        avg_loss = loss.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()

        rs = abs(avg_gain / avg_loss)
        rsi = 100 - (100 / (1 + rs))

        rsi4cl = rsi[-len(self.data['candles']):]
        # set rsi attribute in each candle of the CandleList
        ix = 0
        for c, v in zip(self.data['candles'], rsi4cl):
            self.data['candles'][ix]['rsi'] = round(v, 2)
            ix += 1
        cl_logger.debug("Done calc_rsi")

    def calc_rsi_bounces(self):
        '''Calculate the number of times that the
        price has been in overbought (>70) or
        oversold (<30) regions

        Returns:
            dict:
                 {number: 3
                 lengths: [4,5,6]}
            Where number is the number of times price
            has been in overbought/oversold and lengths list
            is formed by the number of candles that the price
            has been in overbought/oversold each of the times
            sorted from older to newer
        '''
        adj = False
        num_times = 0
        length = 0
        lengths = []

        for c in self.data['candles']:
            if c['rsi'] is None:
                raise Exception("RSI values are not defined for this Candlelist, "
                                "run calc_rsi first")
            if self.type is None:
                raise Exception("type is not defined for this Candlelist")

            if self.type == 'short':
                if c['rsi'] > 70 and adj is False:
                    num_times += 1
                    length = 1
                    adj = True
                elif c['rsi'] > 70 and adj is True:
                    length += 1
                elif c['rsi'] < 70:
                    if adj is True: lengths.append(length)
                    adj = False
            elif self.type == 'long':
                if c['rsi']<30 and adj is False:
                    num_times += 1
                    length = 1
                    adj=True
                elif c['rsi'] < 30 and adj is True:
                    length += 1
                elif c['rsi'] > 30:
                    if adj is True: lengths.append(length)
                    adj = False

        if adj is True and length>0: lengths.append(length)

        if num_times != len(lengths): raise Exception("Number of times" \
                                                      "and lengths do not" \
                                                      "match")
        return { 'number' : num_times,
                 'lengths' : lengths}

    def get_length_candles(self)->int:
        '''Function to calculate the length of CandleList in number of candles.'''
        return len(self.data['candles'])

    def get_length_pips(self)->int:
        '''Function to calculate the length of CandleList in number of pips

        Returns:
            Length in number of pips
        '''
        start_cl = self.data['candles'][0]
        end_cl = self.data['candles'][-1]

        (first, second) = self.data['instrument'].split("_")
        round_number = None
        if first == 'JPY' or second == 'JPY':
            round_number = 2
        else:
            round_number = 4

        start_price = round(float(start_cl['mid']['c']), round_number)
        end_price = round(float(end_cl['mid']['c']), round_number)

        diff = (start_price-end_price)*10**round_number

        return abs(int(round(diff, 0)))

    def get_pivotlist(self, th_bounces: float):
        '''Function to obtain a pivotlist object containing pivots identified using the
        Zigzag indicator.

        Arguments:
            th_bounces: Value used by ZigZag to identify pivots. The lower the
                        value the higher the sensitivity

        Returns:
            PivotList object
        '''

        cl_logger.debug("Running get_pivotlist")

        x = []
        values = []
        for i in range(len(self.data['candles'])):
            x.append(i)
            values.append(float(self.data['candles'][i]['mid']['c']))

        yarr = np.array(values)
        pivots = peak_valley_pivots(yarr, th_bounces,
                                    th_bounces*-1)
        pl = PivotList(parray=pivots,
                       clist=self)
        cl_logger.debug("Done get_pivotlist")
        return pl

    def slice(self, start : datetime = None, end : datetime = None):
        '''Function to slice self on a date interval. It will return the sliced CandleList

        Arguments:
            start: Slice the CandleList from this start datetime. It will create a new CandleList starting
                   from this datetime. If 'end' is not defined, then it will slice the CandleList from 'start'
                   to the end of the CandleList.
            end: If 'start' is not defined, then it will slice from beginning of CandleList to 'end'.

        Returns:
            CandleList object

        Raises
        ------
        Exception
            If start > end
        '''

        sliced_clist = []
        if start is not None and end is None:
            sliced_clist = [c for c in self.data['candles'] if c['time'] >= start]
        elif start is not None and end is not None:
            if start > end:
                raise Exception("Start is greater than end. Can't slice this CandleList")
            sliced_clist = [c for c in self.data['candles'] if c['time'] >= start and c['time'] <= end]
        elif start is None and end is not None:
            sliced_clist = [c for c in self['candles'] if c['time'] <= end ]
        new_dict = {}
        new_dict['candles'] = sliced_clist
        new_dict['instrument'] = self.data['instrument']
        new_dict['granularity'] = self.data['granularity']

        cl = CandleList(new_dict,
                        type=self.type)

        return cl

    def improve_resolution(self, price : float, min_dist : int, part : str ='closeAsk')->list:
        '''Function used to improve the resolution of the identified maxima/minima. This function will select
        the candle closer to 'price' when there are 2 candles less than 'min_dist' apart

        Arguments:
            price : Price that will be used as the reference to select one of the candles
            min_dist : minimum distance between the identified max/min
            part: Candle part used for the calculation

        Returns:
            list containing the selected candles
        '''

        min_distDelta=None
        if min_dist is not None:
            # convert the min_dist integer to a timedelta
            min_distDelta = periodToDelta(ncandles=min_dist,
                                          timeframe=self.granularity)

        list_c=self.clist
        res = [x.time - y.time for x, y in zip(list_c, list_c[1:])]
        below = []  # below will contain the list_c indexes separated by <min_dist
        ix = 0
        for i in res:
            i = abs(i)
            if min_distDelta is not None:
                if i < min_distDelta:
                    below.append((ix, ix + 1))
            else:
                below.append((ix,ix+1))
            ix += 1

        remove_l = [] #list with the indexes to remove
        if below:
            for i in below:
                x0 = getattr(list_c[i[0]], part)
                x1 = getattr(list_c[i[1]], part)
                diff0=abs(x0-price)
                diff1=abs(x1-price)
                #ix to be removed: the furthest
                # from self.price
                if diff0>diff1:
                    remove_l.append(i[0])
                elif diff1>diff0:
                    remove_l.append(i[1])
                elif diff1==diff0:
                    remove_l.append(i[0])

        if remove_l:
            sorted_removel=sorted(list(set(remove_l)))
            list_c = [i for j, i in enumerate(list_c) if j not in sorted_removel]

        return list_c

    def calc_itrend(self):
        '''Function to calculate the datetime for the start of this CandleList, assuming that this
        CandleList is trending. This function will calculate the start of the trend by using the self.get_pivots
        function

        Returns:
            Merged segment containing the trend_i
        '''
        cl_logger.debug("Running calc_itrend")
        outfile = "{0}/pivots/{1}.calc_it.allpivots.png".format(gparams.outdir,
                                                                self.data['instrument'].replace(' ', '_'))

        pivots = self.get_pivotlist(th_bounces=pivots_params.th_bounces,
                                    outfile=outfile)

        # merge segments
        for p in reversed(pivots.plist):
            adj_t = p.adjust_pivottime(clistO=pivots.clist)
            # get new CandleList with new adjusted time for the end
            start = pivots.clist.data['candles'][0]['time']
            newclist = pivots.clist.slice(start= start,
                                          end=adj_t)
            newp = newclist.get_pivotlist(pivots_params.th_bounces).plist[-1]
            newp.merge_pre(slist=pivots.slist,
                           n_candles=pivots_params.n_candles,
                           diff_th=pivots_params.diff_th)
            return newp.pre

        cl_logger.debug("Done clac_itrend")

    def get_lasttime(self, hrarea):
        '''Function to get the datetime for last time that price has been above/below a HArea

        Arguments:
            hrarea : HArea object used to calculate the lasttime

        Returns:
            Will return the last time the price was above/below the self.SR.
            Price is considered to be above (for short trades) the self.SR when candle's lowAsk is
            above self.SR.upper and considered to be below (for long trades) the self.SR when candle's
            highAsk is below sel.SR.below.

            Returned datetime will be the datetime for the first candle in self.clist
            if last time was not found
        '''

        if self.type == "short":
            position = 'above'
        if self.type == "long":
            position = 'below'

        last_time = hrarea.last_time(clist=self.data['candles'],
                                     position=position)

        # if last_time is not defined in this CandleList then assign the time for the first candle
        if last_time is None:
            last_time = self.data['candles'][0]['time']

        return last_time

    def get_highest(self)->float:
        '''Function to calculate the highest
        price in this CandleList

        Returns:
            highest price
        '''

        max = 0.0
        for c in self.data['candles']:
            price = float(c['mid']['c'])
            if price > max:
                max = price

        return max

    def get_lowest(self)->float:
        '''Function to calculate the lowest
        price in this CandeList

        Returns:
            lowest price
        '''

        min = None
        for c in self.data['candles']:
            price = float(c['mid']['c'])
            if min is None:
                min = price
            else:
                if price < min:
                    min = price
        return min