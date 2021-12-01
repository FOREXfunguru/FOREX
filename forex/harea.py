import logging

from datetime import timedelta,datetime
from os import getcwd
from api.oanda.connect import Connect
from ast import literal_eval
from forex.params import harea_params, gparams
from typing import List

import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pdb

# create logger
h_logger = logging.getLogger(__name__)
h_logger.setLevel(logging.INFO)

class HArea(object):
    '''
    Class to represent a horizontal area in the chart

    Class variables
    ---------------
    price : Price in the chart used as the middle point that will be extended on both sides a certain
            number of pips
    instrument : Instrument for this CandleList (i.e. AUD_USD or EUR_USD etc...)
    granularity : Granularity for this CandleList (i.e. D, H12, H8 etc...)
    pips : Number of pips above/below self.price to calculate self.upper and self.lower
    upper : Upper limit price of area
    lower : Lower limit price of area
    no_pivots : Number of pivots bouncing on self
    tot_score : Total score, which is the sum of scores of all pivots on this HArea
    ser_data_obj : ser_data_obj with serialized data
    '''

    def __init__(self, price: float, instrument: str, granularity: str, pips: int, no_pivots: int=None,
                 tot_score: int=None, ser_data_obj=None):

        (first, second) = instrument.split("_")
        self.instrument = instrument
        round_number = None
        divisor = None
        if first == 'JPY' or second == 'JPY':
            round_number = 2
            divisor = 100
        else:
            round_number = 4
            divisor = 10000
        price = round(price, round_number)
        self.price = price
        self.granularity = granularity
        self.no_pivots = no_pivots
        self.tot_score = tot_score

        self.ser_data_obj = ser_data_obj
        self.upper = round(price+(pips/divisor), 4)
        self.lower = round(price-(pips/divisor), 4)

    def last_time(self, clist: List, position: str)->datetime:
        '''Function that returns the datetime of the moment where prices were over/below this HArea.

        Arguments:
            clist: List with Candles
            position: This parameter controls if price should cross the HArea.upper for 'above'
                      or HArea.lower for 'below'
                      Possible values are: 'above' or 'below'

        Returns:
            datetime the price crosses the HArea'''
        count = 0
        for c in reversed(clist):
            count += 1
            # Last time has to be at least forexparams.min candles before
            if count <= harea_params.min :
                continue
            if position == 'above':
                price = float(c['mid']['l'])
                if price > self.upper:
                    return c['time']
            elif position == 'below':
                price = float(c['mid']['h'])
                if price < self.lower:
                    return c['time']

    def get_cross_time(self, candle, granularity='M30')->datetime:
        '''
        This function is used get the time that the candle
        crosses (go through) HArea

        Arguments:
            candle : Dict with the candle data that crosses the HArea
            granularity : To what granularity we should descend

        Returns:
            crossing time.
            n.a. if crossing time could not retrieved. This can happens
            when there is an artefactual jump in Oanda's data
        '''
        # consider both Ask and bid
        cross = False
        if float(candle['mid']['l']) <= self.price <= float(candle['mid']['h']):
            cross = True

        if cross is True:
            delta = None
            if self.granularity == "D":
                delta = timedelta(hours=24)
            else:
                fgran = self.granularity.replace('H', '')
                delta = timedelta(hours=int(fgran))

            cstart = candle['time']
            cend = cstart+delta
            conn = Connect(instrument=self.instrument,
                           granularity=granularity)  # 'M30' is the default
           
            h_logger.debug("Fetching data from API")
            ser_file = None
            if gparams.ser_data_file_gran:
                ser_file = gparams.ser_data_file_gran

            res = conn.query(start=cstart.isoformat(),
                             end=cend.isoformat(),
                             indir=ser_file)

            seen = False
            for c in res['candles']:
                if float(candle['mid']['l']) <= self.price <= float(candle['mid']['h']):
                    seen = True
                    return c['time']
            if seen is False:
                return 'n.a.'
        else:
            return 'n.a.'

    def __repr__(self):
        return "HArea"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str

class HAreaList(object):
    '''
    Class that represents a list of HArea objects

    Class variables
    ---------------
    halist : List of HArea objects
    '''

    def __init__(self, halist):
        self.halist = halist

    def onArea(self, candle):
        '''Function that will check which (if any) of the HArea objects
        in this HAreaList will overlap with 'candle'.

        See comments in code to understand what is considered
        an overlap

        Arguments:
            candle: Candle object

        Returns:
            An HArea object overlapping with 'candle' and the ix
            in self.halist for this HArea.
            None if there are no HArea objects overlapping'''
        pdb.set_trace()
        onArea_hr = sel_ix = None
        ix = 0
        for harea in self.halist:
            if harea.price <= float(candle.mid['h']) and harea.price >= float(candle.mid['l']):
                onArea_hr = harea
                sel_ix = ix
            ix += 1
        pdb.set_trace()
        return onArea_hr, sel_ix

    def print(self):
        '''
        Function to print out basic information on each of the
        HArea objects in the HAreaList

        Returns
        -------
        String with stringified HArea objects
        '''
        res ="#pair timeframe upper-price-lower no_pivots tot_score\n"
        for harea in self.halist:
            res += "{0} {1} {2}-{3}-{4} {5} {6}\n".format(harea.instrument,
                                                          harea.granularity,
                                                          harea.upper,
                                                          harea.price,
                                                          harea.lower,
                                                          harea.no_pivots,
                                                          harea.tot_score)
        return res.rstrip("\n")

    def plot(self, clO, outfile):
        """
        Plot this HAreaList

        Parameters
        ----------
        clO : CandeList object
              Used for plotting
        outfile : str
                  Output file
        """
        prices, datetimes = ([] for i in range(2))
        for c in clO.data['candles']:
            prices.append(c[gparams.general])
            datetimes.append(c['time'])

        # getting the fig size from settings
        figsize = literal_eval(gparams.size)
        # massage datetimes so they can be plotted in X-axis
        x = [mdates.date2num(i) for i in datetimes]

        # plotting the prices for part
        fig = plt.figure(figsize=figsize)
        ax = plt.axes()
        ax.plot(datetimes, prices, color="black")

        xmax1 = len(datetimes)-1
        prices = [x.price for x in self.halist]

        # now, print an horizontal line for each S/R
        ax.hlines(prices, datetimes[0], datetimes[-1], color="green")

        fig.savefig(outfile, format='png')


    def __repr__(self):
        return "HAreaList"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str