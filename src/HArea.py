import numpy as np
import pdb
import matplotlib
import peakutils
import datetime
from OandaAPI import OandaAPI
matplotlib.use('PS')
import matplotlib.pyplot as plt


class HArea(object):
    '''
    Class to represent a horizontal area in the chart

    Class variables
    ---------------
    price : float, Required
            Price in the chart used as the middle point that will be extended on both sides a certain
            number of pips
    pips : float, Required
          Number of pips to extend on each side
    instrument : str, Optional
                 Instrument for this CandleList (i.e. AUD_USD or EUR_USD etc...)
    granularity : str, Optional
                Granularity for this CandleList (i.e. D, H12, H8 etc...)
    upper : float, Optional
           Upper limit of area
    lower : float, Optional
            Lower limit of area
    '''

    def __init__(self, price, pips, instrument, granularity):

        (first, second) = instrument.split("_")
        self.instrument=instrument
        round_number = None
        divisor = None
        if first == 'JPY' or second == 'JPY':
            round_number = 2
            divisor=100
        else:
            round_number = 4
            divisor=10000
        price = round(price, round_number)
        self.price = price
        self.pips = pips
        self.granularity = granularity
        self.upper=price+(pips/divisor)
        self.lower=price-(pips/divisor)

    def number_bounces(self, datetimes, prices, threshold=0.60, min_dist=10, outfile='bounces.png'):
        '''
        Function used to calculate the datetime for previous bounces in this area

        Parameters
        ----------
        datetimes : list
                Lisf of datetimes associated to each of the prices
        prices : list
                List of prices used to calculate the bounces
        threshold : float
                    Threshold for detecting peaks. Default : 0.60
        min_dist : float
                   Threshold for minimum distance for detecting peaks. Default : 10
        outfile : file
                Filename for output .png file

        Returns
        -------
        file : png file with identified bounces
        list : list of tuples containing datetime and value for each peak/bounce
        '''
        cb = np.array(prices)
        max = peakutils.indexes(cb, thres=threshold, min_dist=min_dist)
        min = peakutils.indexes(-cb, thres=threshold, min_dist=min_dist)

        fig = plt.figure(figsize=(20, 10))
        ax = plt.axes()
        ax.plot(datetimes, prices, color="black")

        pdb.set_trace()
        bounces=[]
        for ix in max:
            if prices[ix]>=self.lower and prices[ix]<=self.upper:
                bounces.append((datetimes[ix],prices[ix]))
                plt.scatter(datetimes[ix], prices[ix], s=50)

        for ix in min:
            if prices[ix] <= self.upper and prices[ix] >= self.lower:
                bounces.append((datetimes[ix], prices[ix]))
                plt.scatter(datetimes[ix], prices[ix], s=50)

        fig.savefig(outfile, format='png')

        return bounces,outfile

    def last_time(self, clist, position, part='openAsk'):
        '''
        Function that returns the datetime of the moment where prices were over/below this HArea

        Parameters
        ----------
        clist   CandleList object
                List with Candles
        position    This parameter controls if price should cross the HArea.upper for 'above'
                    or HArea.lower for 'below'
                    Possible values are: 'above' or 'below'
        part : str
               What part of the candle will be used for calculating the length in pips
               Possible values are: 'openAsk', 'closeAsk', 'lowAsk', 'openBid', 'closeBid'.
               Default: openAsk

        Return
        ------
        datetime object of the moment that the price crosses the HArea
        '''

        for c in reversed(clist.clist):
            price=getattr(c, part)
            if position == 'above':
                if price > self.upper:
                    return c.time
            elif position == 'below':
                if price < self.below:
                    return c.time

    def get_bounce_feats(self, clist, direction):
        '''
        This function is used to calculate some bounce
        features, where bounce is defined with respect
        to the HArea

        Parameters
        ----------
        clist :   CandleList object
                  List with Candles
        direction : str
                    Direction of the trend. Possible values are 'up'/'down'

        Returns
        ------
        int  number of candles of the bounce
        int  number of pips from HRarea.price to highest/lowest point reached by
             the bounce
        '''

        highest=0
        inn_bounce=0
        entered=False

        for c in reversed(clist.clist):
            #check if candle is within body
            if c.openAsk <= self.price <= c.closeAsk and entered is False:
                if direction=='up': highest=c.highAsk
                elif direction=='down': highest=c.lowAsk
                inn_bounce+=1
                entered=True
            elif entered is True and direction=='down' and (c.openAsk>self.price and c.closeAsk > self.price):
                break
            elif entered is True and direction=='up' and (c.openAsk<self.price and c.closeAsk < self.price):
                break
            elif entered is True:
                inn_bounce+=1
                if direction == 'up' and c.highAsk > highest:
                    highest = c.highAsk
                elif direction == 'down' and c.lowAsk < highest:
                    highest = c.lowAsk

        (first, second) = self.instrument.split("_")
        round_number = None
        if first == 'JPY' or second == 'JPY':
            round_number = 2
        else:
            round_number = 4

        highest = round(highest, round_number)
        s_rprice = round(self.price, round_number)

        diff = (highest - s_rprice) * 10 ** round_number

        return (inn_bounce,abs(int(round(diff, 0))))

    def get_cross_time(self, candle, granularity='M30'):
        '''
        This function is used get the time that the candle
        crosses (go through) HArea

        Parameters
        ----------
        candle :   Candle object that crosses the HArea
        granularity : To what granularity we should descend

        Returns
        ------
        datetime object with crossing time
        '''


        if candle.lowAsk <= self.price <= candle.highAsk:
            delta=None
            if self.granularity=="D":
                delta = datetime.timedelta(days=self.granularity)
            else:
                fgran=self.granularity.replace('H','')
                delta=datetime.timedelta(hours=int(fgran))

            cstart=candle.time
            cend=cstart+delta
            oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                             instrument=self.instrument,
                             granularity=granularity,
                             dailyAlignment=22,
                             alignmentTimezone='Europe/London',
                             start=cstart.isoformat(),
                             end=cend.isoformat())
            candle_list = oanda.fetch_candleset()
            for c in candle_list:
                if c.lowAsk <= self.price <= c.highAsk:
                    return c.time

