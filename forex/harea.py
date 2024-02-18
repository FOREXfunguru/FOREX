import logging
import sys

from datetime import timedelta, datetime
from api.oanda.connect import Connect
from params import gparams
from forex.candle import Candle

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

h_logger = logging.getLogger(__name__)
h_logger.setLevel(logging.INFO)


class HArea(object):
    '''Class to represent a horizontal area in the chart.

    Class variables:
        price: Price in the chart used as the middle point that will be
               extended on both sides a certain number of pips
        instrument: Instrument for this CandleList 
        granularity: Granularity for this CandleList (i.e. D, H12, H8 etc...)
        pips: Number of pips above/below self.price to calculate self.upper
              and self.lower
        upper: Upper limit price of area
        lower: Lower limit price of area
        no_pivots: Number of pivots bouncing on self
        tot_score: Total score, which is the sum of scores of all pivots on
                   this HArea
    '''
    __slots__ = ["price", "instrument", "granularity", "pips",
                 "no_pivots", "tot_score", 'upper', 'lower']

    def __init__(self, price: float, instrument: str,
                 granularity: str, pips: int, no_pivots: int = None,
                 tot_score: int = None):

        try:
            (first, second) = instrument.split("_")
        except ValueError:
            logging.exception(f"Incorrect '_' split for instrument:{instrument}")
            sys.exit(1)
        self.instrument = instrument
        round_number = None
        divisor = None
        if first == "JPY" or second == "JPY":
            round_number = 2
            divisor = 100
        else:
            round_number = 4
            divisor = 10000
        price = round(price, round_number)
        self.price = price
        self.pips = pips
        self.granularity = granularity
        self.no_pivots = no_pivots
        self.tot_score = tot_score
        self.upper = round(price+(pips/divisor), 4)
        self.lower = round(price-(pips/divisor), 4)

    def get_cross_time(self, candle: Candle, granularity='M30') -> datetime:
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
            if res.candles:
                for c in res:
                    if c.l <= self.price <= c.h:
                        seen = True
                        return c.time
            if seen is False:
                return candle.time
        else:
            return 'n.a.'

    def __repr__(self):
        return "HArea"

    def __str__(self):
        out_str = ""
        for attr in self.__slots__:
            out_str += f"{attr}:{getattr(self, attr)} "
        return out_str


class HAreaList(object):
    """Class that represents a list of HArea objects.

    Class variables:
        halist : List of HArea objects
    """
    __slots__ = ["halist"]

    def __init__(self, halist):
        self.halist = halist

    def onArea(self, candle: Candle):
        '''Function that will check which (if any) of the HArea objects
        in this HAreaList will overlap with 'candle'.

        See comments in code to understand what is considered
        an overlap

        Arguments:
            candle: Candle that will be checked

        Returns:
            An HArea object overlapping with 'candle' and the ix
            in self.halist for the HArea being crossed. This ix is expressed
            from the HArea with the lowest price to the highest price and
            starting from 0.
            So if 'sel_ix'=2, then it will be the third HArea
            None if there are no HArea objects overlapping'''
        onArea_hr = sel_ix = None
        ix = 0
        seen = False
        for harea in self.halist:
            if harea.price <= float(candle.h) and \
                 harea.price >= float(candle.l):
                if seen:
                    logging.warn("More than one HArea crosses this candle")
                onArea_hr = harea
                sel_ix = ix
                seen = True
            ix += 1
        return onArea_hr, sel_ix

    def print(self) -> str:
        '''Function to print out basic information on each of the
        HArea objects in the HAreaList

        Returns:
            String with stringified HArea objects
        '''
        res = "#pair timeframe upper-price-lower no_pivots tot_score\n"
        for harea in self.halist:
            res += "{0} {1} {2}-{3}-{4} {5} {6}\n".format(harea.instrument,
                                                          harea.granularity,
                                                          harea.upper,
                                                          harea.price,
                                                          harea.lower,
                                                          harea.no_pivots,
                                                          harea.tot_score)
        return res.rstrip("\n")

    def plot(self, clO, outfile: str) -> None:
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
