'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
import pandas as pd
import matplotlib
import datetime
import logging
import pickle
from utils import *
from params import clist_params
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

matplotlib.use('PS')

logging.basicConfig(level=logging.INFO)

# create logger
cl_logger = logging.getLogger(__name__)
cl_logger.setLevel(logging.INFO)


class Candle(object):
    """Class representing a particular Candle"""
    def __init__(self, **kwargs) -> None:
        allowed_keys = ['complete', 'volume', 'time', 'o', 'h', 'c', 'l']  # allowed arbitrary argsa
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        numeric = ['o', 'h', 'c', 'l']
        self.__dict__.update((k, float(v)) for k,v in self.__dict__.items() if k in numeric)
        if isinstance(self.__dict__['time'], str):
            self.__dict__.update({'time': datetime.strptime(self.__dict__['time'], '%Y-%m-%dT%H:%M:%S')})
        self._colour = self._set_colour()
        self._perc_body = self._calc_perc_body()

    @property
    def colour(self) -> str:
        """Candle's body colour"""
        return self._colour
  
    @property
    def perc_body(self) -> float:
        """Candle's body percentage"""
        return self._perc_body

    def _set_colour(self) -> str:
        if self.o < self.c:
            return "green"
        elif self.o > self.c:
            return "red"
        else:
            return "undefined"
    
    def _calc_perc_body(self) -> float:
        height = self.h - self.l
        if height == 0:
            return 0
        body = abs(self.o - self.c)
        return round((body * 100) / height, 2)

    def indecision_c(self, ic_perc: int = 10) -> bool:
        """Function to check if 'self' is an indecision candle.

        Args:
            ic_perc : Candle's body percentage below which the candle will be considered 
                      indecision candle.
        """
        if self.perc_body <= ic_perc:
            return True
        else:
            return False
    
    def height(self, pair):
        """Function to calculate the number of pips between self.h and self.l"""
        return abs(float(calculate_pips(pair, self.l-self.h)))
    
    def __repr__(self):
        return "Candle"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str


class CandleList(object):
    """Class containing a list of Candles.

    Class variables:
        instrument: i.e. 'AUD_USD'
        granularity: i.e. 'D'
        candles: List of Candle objects
        type: Type of this CandleList. Possible values are 'long'/'short'"""

    def __init__(self, instrument: str, granularity: str, data: list = None,
                 candles=None):
        """Constructor

        Arguments:
            data: list of Dictionaries, each dict containing data for a Candle
        
        self.times will be a list of datetime objects
        """
        if candles:
            self.candles = candles
            self.times = [c.time for c in candles]
        elif data:
            self.candles = [Candle(**d) for d in data]
            self.times = [try_parsing_date(d['time']) if isinstance(d['time'],
                                                                     str) else d['time'] for d in data]
        else:
            self.candles = []
            self.times = []
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
    
    def __getitem__(self, adatetime: datetime)->Candle:
        if not isinstance(adatetime, datetime):
            raise ValueError("A datetime object is needed!")
        fdt = None
        if adatetime not in self.times:
            dtp1 = (adatetime + timedelta(hours=1))
            dtm1 = (adatetime - timedelta(hours=1))
            if dtp1 in self.times:
                fdt = dtp1
            elif dtm1 in self.times:
                fdt = dtm1
        else:
            fdt = adatetime
        if fdt:
            return self.candles[self.times.index(fdt)]
    
    def __index__(self, adatetime: datetime) -> int:
        fdt = None
        if adatetime not in self.times:
            dtp1 = (adatetime + timedelta(hours=1))
            dtm1 = (adatetime - timedelta(hours=1))
            if dtp1 in self.times:
                fdt = dtp1
            elif dtm1 in self.times:
                fdt = dtm1
        else:
            fdt = adatetime
        if fdt:
            return self.times.index(fdt)
        else:
            raise ValueError(f"{adatetime} not in self.times")
    
    def __len__(self):
        return len(self.candles)
    
    def __add__(self, ClO):

        clist = self.candles + ClO.candles
        clist = [x.__dict__ for x in clist]
        newClO = CandleList(instrument=self.instrument,
                            granularity=self.granularity,
                            data=clist)
        return newClO
    
    def _guess_type(self) -> str:
        if len(self.candles) == 0:
            return None
        price_1st = self.candles[0].c
        price_last = self.candles[-1].c
        if price_1st > price_last:
            return 'short'  # or downtrend
        elif price_1st < price_last:
            return 'long'  # or uptrend
        
    def calc_rsi(self):
        '''Calculate the RSI for a certain candle list.'''
        cl_logger.debug("Running calc_rsi")

        series = [c.c for c in self.candles]

        df = pd.DataFrame({'close': series})
        chg = df['close'].diff(1)

        gain = chg.mask(chg < 0, 0)
        loss = chg.mask(chg > 0, 0)

        rsi_period = clist_params.rsi_period
        avg_gain = gain.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
        avg_loss = loss.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()

        rs = abs(avg_gain / avg_loss)
        rsi = 100 - (100 / (1 + rs))

        rsi4cl = rsi[-len(self.candles):]
        # set rsi attribute in each candle of the CandleList
        ix = 0
        for c, v in zip(self.candles, rsi4cl):
            self.candles[ix].rsi = round(v, 2)
            ix += 1
        cl_logger.debug("Done calc_rsi")

    def pickle_dump(self, outfile: str) -> str:
        """Function to pickle this particular CandleList
        
        Arguments:
            outfile: Path used to pickle
            
        Returns:
            path to file with pickled data
        """
        
        pickle_out = open(outfile, "wb")
        pickle.dump(self, pickle_out)
        pickle_out.close()

        return outfile

    @classmethod
    def pickle_load(self, infile: str):
        '''Function to pickle this particular CandleList
        
        Arguments:
            infile: Path used to load in pickled data
            
        Returns:
            inclO: CandleList object    
        '''
        pickle_in = open(infile, "rb")
        inclO = pickle.load(pickle_in)

        return inclO

    def calc_rsi_bounces(self) -> dict:
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
        num_times, length = 0, 0
        lengths = []

        for c in self.candles:
            if c.rsi is None:
                raise Exception("RSI values are not defined for this Candlelist, "
                                "run calc_rsi first")
            if self.type is None:
                raise Exception("type is not defined for this Candlelist")

            if self.type == 'short':
                if c.rsi > 70 and adj is False:
                    num_times += 1
                    length = 1
                    adj = True
                elif c.rsi > 70 and adj is True:
                    length += 1
                elif c.rsi < 70:
                    if adj is True: lengths.append(length)
                    adj = False
            elif self.type == 'long':
                if c.rsi < 30 and adj is False:
                    num_times += 1
                    length = 1
                    adj = True
                elif c.rsi < 30 and adj is True:
                    length += 1
                elif c.rsi > 30:
                    if adj is True: 
                        lengths.append(length)
                    adj = False

        if adj is True and length > 0:
            lengths.append(length)

        if num_times != len(lengths): raise Exception("Number of times" \
                                                      "and lengths do not" \
                                                      "match")
        return {'number': num_times,
                'lengths': lengths}

    def get_length_pips(self) -> int:
        '''Function to calculate the length of CandleList in number of pips'''

        start_cl = self.candles[0]
        end_cl = self.candles[-1]

        (first, second) = self.instrument.split("_")
        round_number = None
        if first == 'JPY' or second == 'JPY':
            round_number = 2
        else:
            round_number = 4

        start_price = round(float(start_cl.c), round_number)
        end_price = round(float(end_cl.c), round_number)

        diff = (start_price-end_price)*10**round_number

        return abs(int(round(diff, 0)))

    def slice(self, start: datetime, end: datetime, inplace: bool = False) -> 'CandleList':
        """Function to slice self on a date interval. It will modify inplace the CandleList.

        Arguments:
            start: Slice the CandleList from this start datetime.
            end:  This CandleList will have this 'end' datetime.

        Raises
        ------
        Exception
            If start > end
        """
        if self.granularity == "D":
            delta = timedelta(hours=24)
        else:
            fgran = self.granularity.replace('H', '')
            delta = timedelta(hours=int(fgran))

        while not self.__getitem__(start):
            start = start+delta
        while not self.__getitem__(end):
            end = end+delta
        start_ix = self.__index__(start)
        end_ix = self.__index__(end)
        if not inplace:
            cl = CandleList(instrument=self.instrument,
                            granularity=self.granularity,
                            candles=self.candles[start_ix:end_ix+1])
            return cl
        else:
            self.candles = self.candles[start_ix:end_ix+1]
            self.times = self.times[start_ix:end_ix+1]
            self._type = self._guess_type()
            return self

    def get_lasttime(self, price: float, type: str) -> datetime:
        """Function to get the datetime for last time that price has been above/below a price level

        Arguments:
            price: value to calculate the last time in this CandleList the price was above/below
            trade type: either long/short
        """
       
        count = 0
        for c in reversed(self.candles):
            count += 1
            # Last time has to be at least forexparams.min candles before
            if count <= clist_params.min:
                continue
            if type == 'long':
                if c.h < price:
                    return c.time
            elif type == 'short':
                if c.l > price:
                    return c.time
        
        return self.candles[0].time

    def get_highest(self) -> float:
        """Function to calculate the highest
        price in this CandleList

        Returns:
            highest price
        """
        max = 0.0
        for cl in self.candles:
            price = cl.c
            if price > max:
                max = price

        return max

    def get_lowest(self) -> float:
        '''Function to calculate the lowest
        price in this CandeList

        Returns:
            lowest price
        '''
        min = None
        for cl in self.candles:
            price = cl.c
            if min is None:
                min = price
            else:
                if price < min:
                    min = price
        return min

    