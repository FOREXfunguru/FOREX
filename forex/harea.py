import logging

from datetime import timedelta,datetime
from api.oanda.connect import Connect
from forex.params import harea_params, gparams
from typing import List

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pdb

# create logger
h_logger = logging.getLogger(__name__)
h_logger.setLevel(logging.INFO)

class HArea(object):
    '''Class to represent a horizontal area in the chart.

    Class variables:
        price: Price in the chart used as the middle point that will be extended on both sides a certain
               number of pips
        instrument: Instrument for this CandleList (i.e. AUD_USD or EUR_USD etc...)
        granularity: Granularity for this CandleList (i.e. D, H12, H8 etc...)
        pips: Number of pips above/below self.price to calculate self.upper and self.lower
        upper: Upper limit price of area
        lower: Lower limit price of area
        no_pivots: Number of pivots bouncing on self
        tot_score: Total score, which is the sum of scores of all pivots on this HArea
    '''
    def __init__(self, price: float, instrument: str, granularity: str, pips: int, no_pivots: int=None,
                 tot_score: int=None):

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
        self.upper = round(price+(pips/divisor), 4)
        self.lower = round(price-(pips/divisor), 4)

    def get_cross_time(self, candle, granularity='M30')->datetime:
        '''This function is used get the time that the candle
        crosses (go through) HArea

        Arguments:
            candle: Candle crossing the HArea
            granularity: To what granularity we should descend

        Returns:
            crossing time.
            n.a. if crossing time could not retrieved. This can happens
            when there is an artifactual jump in Oanda's data
        '''
        if candle.l <= self.price <= candle.h:
            delta = None
            if self.granularity == "D":
                delta = timedelta(hours=24)
            else:
                fgran = self.granularity.replace('H', '')
                delta = timedelta(hours=int(fgran))

            cstart = candle.time
            cend = cstart+delta
            conn = Connect(instrument=self.instrument,
                           granularity=granularity)
           
            h_logger.debug("Fetching data from API")
            res = conn.query(start=cstart.isoformat(),
                             end=cend.isoformat())

            seen = False
            for c in res:
                if c.l <= self.price <= c.h:
                    seen = True
                    return c.time

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
    '''Class that represents a list of HArea objects.

    Class variables:
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
        onArea_hr = sel_ix = None
        ix = 0
        for harea in self.halist:
            if harea.price <= float(candle.mid['h']) and harea.price >= float(candle.mid['l']):
                onArea_hr = harea
                sel_ix = ix
            ix += 1
        pdb.set_trace()
        return onArea_hr, sel_ix

    def print(self)->str:
        '''Function to print out basic information on each of the
        HArea objects in the HAreaList

        Returns:
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

    def plot(self, clO, outfile: str)->None:
        """Plot this HAreaList

        Args:
            clO : CandeList object
                  Used for plotting
            outfile : Output file
        """
        prices, datetimes = ([] for i in range(2))
        for c in clO.candles:
            prices.append(c.c)
            datetimes.append(c.time)

        # massage datetimes so they can be plotted in X-axis
        x = [mdates.date2num(i) for i in datetimes]

        # plotting the prices for part
        fig = plt.figure(figsize=gparams.size)
        ax = plt.axes()
        ax.plot(datetimes, prices, color="black")

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