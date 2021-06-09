import logging

from datetime import timedelta,datetime
from api.oanda.connect import Connect
from config import CONFIG
from ast import literal_eval

import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# create logger
h_logger = logging.getLogger(__name__)
h_logger.setLevel(logging.INFO)

class HArea(object):
    '''
    Class to represent a horizontal area in the chart

    Class variables
    ---------------
    price : float, Required
            Price in the chart used as the middle point that will be extended on both sides a certain
            number of pips
    instrument : str, Required
                 Instrument for this CandleList (i.e. AUD_USD or EUR_USD etc...)
    granularity : str, Required
                Granularity for this CandleList (i.e. D, H12, H8 etc...)
    pips : int, Required
        Number of pips above/below self.price to calculate self.upper and self.lower
    upper : float, Optional
           Upper limit price of area
    lower : float, Optional
            Lower limit price of area
    no_pivots : int, Optional
                Number of pivots bouncing on self
    tot_score : int, Optional
                Total score, which is the sum of scores of all pivots
                on this HArea
    ser_data_obj : ser_data_obj, Optional
                   ser_data_obj with serialized data
    '''

    def __init__(self, price, instrument, granularity, pips, no_pivots=None,
                 tot_score=None, ser_data_obj=None):

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

    def last_time(self, clist, position):
        '''
        Function that returns the datetime of the moment where prices were over/below this HArea.

        Parameters
        ----------
        clist   list
                List with Candles
        position    This parameter controls if price should cross the HArea.upper for 'above'
                    or HArea.lower for 'below'
                    Possible values are: 'above' or 'below'

        Return
        ------
        datetime object of the moment that the price crosses the HArea
        '''
        count = 0

        for c in reversed(clist):
            count += 1
            # Last time has to be at least self.settings.getint('harea', 'min') candles before
            if count <= CONFIG.getint('harea', 'min'):
                continue
            if position == 'above':
                price = c['lowAsk']
                if price > self.upper:
                    return c['time']
            elif position == 'below':
                price = c['highAsk']
                if price < self.lower:
                    return c['time']

    def get_cross_time(self, candle, granularity='M30'):
        '''
        This function is used get the time that the candle
        crosses (go through) HArea

        Parameters
        ----------
        candle :   Dict with the candle data that crosses the HArea
        granularity : To what granularity we should descend

        Returns
        ------
        datetime object with crossing time.
                 n.a. if crossing time could not retrieved. This can happens
                 when there is an artefactual jump in Oanda's data
        '''
        # consider both Ask and bid
        cross = False
        bit = None
        if candle['lowAsk'] <= self.price <= candle['highAsk']:
            cross = True
            bit = "Ask"
        elif candle['lowBid'] <= self.price <= candle['highBid']:
            cross = True
            bit = "Bid"

        if cross is True:
            delta = None
            if self.granularity == "D":
                delta = timedelta(hours=24)
            else:
                fgran = self.granularity.replace('H', '')
                delta = timedelta(hours=int(fgran))

            cstart = datetime.strptime(candle['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
            cend = cstart+delta
            conn = Connect(instrument=self.instrument,
                           granularity=granularity)  # 'M30' is the default
            h_logger.debug("Fetching data from API")
            ser_file = None
            if CONFIG.has_option('general', 'ser_data_file_gran'):
                ser_file = CONFIG.get('general', 'ser_data_file_gran')
            res = conn.query(start=cstart.isoformat(),
                             end=cend.isoformat(),
                             indir=ser_file)

            seen = False
            part_low = "low{0}".format(bit)
            part_high = "high{0}".format(bit)
            for c in res['candles']:
                low = c[part_low]
                high = c[part_high]
                if low <= self.price <= high:
                    seen = True
                    return datetime.strptime(c['time'],
                                             '%Y-%m-%dT%H:%M:%S.%fZ')
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
    halist : list, Required
            List of HArea objects
    '''

    def __init__(self, halist):
        self.halist = halist

    def onArea(self, candle):
        '''
        Function that will check which (if any) of the HArea objects
        in this HAreaList will overlap with 'candle'.

        See comments in code to understand what is considered
        an overlap

        Parameters
        ----------
        candle: Candle object

        Returns
        -------
        An HArea object overlapping with 'candle' and the ix
        in self.halist for this HArea.
        None if there are no HArea objects overlapping
        '''
        onArea_hr = sel_ix = None
        ix = 0
        for harea in self.halist:
            highAttr = "high{0}".format(CONFIG.get('general', 'bit'))
            lowAttr = "low{0}".format(CONFIG.get('general', 'bit'))
            if harea.price <= getattr(candle, highAttr) and harea.price >= getattr(candle, lowAttr):
                onArea_hr = harea
                sel_ix = ix
            ix += 1

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
            prices.append(c[CONFIG.get('general', 'part')])
            datetimes.append(c['time'])

        # getting the fig size from settings
        figsize = literal_eval(CONFIG.get('images', 'size'))
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