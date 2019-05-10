import numpy as np
import pdb
import matplotlib
import peakutils
import warnings
from datetime import timedelta,datetime
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

    def __improve_resolution(self,x,y,indexes,type,min_dist=5):
        '''
        Function used to improve the resolution of the identified maxima/minima.
        This will rely on peakutils function named 'interpolate' that will basically
        calculate the centroid for the identified maxima/minima. This function can
        be used along with the minimum distance parameter ('min_dist')
        in order to select the maxima/minima that is the highest/lowest from the cluster
        of points that are not separated by more than 'min_dist'

        Parameters
        ----------
        x : Numpy array
            X values, Required
        y : Numpy array
            Y values, Required
        indexes : list
                  Indexes for which the resolution will be improved
                  Required
        type : str
               Type of trade. Possible values are: 'long','short'
        min_dist : int
                   minimum distance between the identified max/min. Default=5

        Returns
        -------
        int : X index/es that need to be removed. None if none index needs to be removed
        '''

        res = [x - y for x, y in zip(indexes, indexes[1:])]
        below = []
        ix = 0
        for i in res:
            i = abs(i)
            if i < min_dist:
                below.append((ix, ix + 1))
            ix += 1

        remove_l = []
        below = list(set(below))
        if below:
            for i in below:
                x0 = i[0]
                x1 = i[1]
                y0 = y[x0]
                y1 = y[x1]
                if type == 'short':
                    #remove the smallest
                    if y0 > y1:
                        remove_l.append(x1)
                    elif y0 < y1:
                        remove_l.append(x0)
                    else:
                        raise Exception("No selection was done!")
                elif type == 'long':
                    if y0 < y1:
                        remove_l.append(x1)
                    elif y0 > y1:
                        remove_l.append(x0)
                    else:
                        raise Exception("No selection was done!")
                ix = +ix
            remove_x = []
            for i in sorted(remove_l):
                remove_x.append(x[indexes[i]])
            pdb.set_trace()
            return sorted(list(set(remove_x)))
        else:
            return None

    def get_bounces(self, datetimes, prices, type, threshold=0.50, min_dist=10):
        '''
        Function used to calculate the datetime for previous bounces in this area

        Parameters
        ----------
        datetimes : list
                Lisf of datetimes associated to each of the prices
        prices : list
                List of prices used to calculate the bounces
        type : str
               Type of trade ('long' or 'short')
        threshold : float
                    Threshold for detecting peaks. Default : 0.50
        min_dist : float
                   Threshold for minimum distance for detecting peaks. Default : 10

        Returns
        -------
        file : png file with identified bounces
        list : list of tuples containing datetime and value for each peak/bounce
        '''
        cb = np.array(prices)
        max = peakutils.indexes(cb, thres=threshold, min_dist=min_dist)
        min = peakutils.indexes(-cb, thres=threshold, min_dist=min_dist)

        in_area_ix=[]

        bounces=[]
        for ix in max:
            if prices[ix]>=self.lower and prices[ix]<=self.upper:
                in_area_ix.append(ix)
                bounces.append((datetimes[ix],prices[ix]))

        for ix in min:
            if prices[ix] <= self.upper and prices[ix] >= self.lower:
                in_area_ix.append(ix)
                bounces.append((datetimes[ix], prices[ix]))

        y=None
        if type=='long':
            y=-cb
        elif type=='short':
            y=cb

        repeat = True
        datetimes_ix=in_area_ix
        fdatetimes_ix=[]
        pdb.set_trace()
        while repeat is True:
            datetimes_ix = self.__improve_resolution(x=np.array(list(range(0, len(datetimes), 1))),
                                                     y=y, type=type, indexes=in_area_ix, min_dist=10)
            if datetimes_ix is not None:
                fdatetimes_ix.append(datetimes_ix)
                in_area_ix=datetimes_ix
            else:
                repeat = False

        if fdatetimes_ix:
            final_bounces=[]
            for d in fdatetimes_ix:
                dt=datetimes[d]
                for b in bounces:
                    b_d=b[0]
                    if dt!=b_d:
                        final_bounces.append(b)

            return final_bounces
        else:
            return bounces

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
                if price < self.lower:
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
        datetime object with crossing time.
                 n.a. if crossing time could not retrieved. This can happens
                 when there is an artifactual jump in the Oanda data
        '''

        if candle.lowAsk <= self.price <= candle.highAsk:
            delta=None
            if self.granularity=="D":
                delta = timedelta(hours=24)
            else:
                fgran=self.granularity.replace('H','')
                delta = timedelta(hours=int(fgran))

            cstart=candle.time
            cend=cstart+delta

            oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                             instrument=self.instrument,
                             granularity=granularity,
                             dailyAlignment=22,
                             alignmentTimezone='Europe/London')

            oanda.run(start=cstart.isoformat(),
                      end=cend.isoformat(),
                      roll=True)

            candle_list = oanda.fetch_candleset()
            for c in candle_list:
                if c.lowAsk <= self.price <= c.highAsk:
                    return c.time
        else:
            return 'n.a.'

