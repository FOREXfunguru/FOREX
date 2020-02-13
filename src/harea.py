import numpy as np
import pdb
import matplotlib
import config
import peakutils
import traceback
import warnings
from zigzag import *
from datetime import timedelta,datetime
from oanda_api import OandaAPI
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
    bounces : list of Candle Objects
              This list contains the candles for bounces bouncing in this area. This member class
              can be initialized using the 'inarea_bounces' method
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
        self.upper=round(price+(pips/divisor),4)
        self.lower=round(price-(pips/divisor),4)

    def last_time(self, clist, position, part='openAsk'):
        '''
        Function that returns the datetime of the moment where prices were over/below this HArea

        Parameters
        ----------
        clist   list
                List with Candles
        position    This parameter controls if price should cross the HArea.upper for 'above'
                    or HArea.lower for 'below'
                    Possible values are: 'above' or 'below'
        part : str
               What part of the candle will be used for calculating the length in pips
               Possible values are: 'openAsk', 'closeAsk', 'lowAsk', 'openBid', 'closeBid', 'lowAsk',
               and 'highAsk'.
               Default: openAsk

        Return
        ------
        datetime object of the moment that the price crosses the HArea
        '''

        for c in reversed(clist):
            price=getattr(c, part)
            if position == 'above':
                pdb.set_trace()
                if price > self.upper:
                    return c.time
            elif position == 'below':
                if price < self.lower:
                    return c.time

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
                 when there is an artifactual jump in Oanda's data
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

            oanda = OandaAPI(url=config.OANDA_API['url'],
                             instrument=self.instrument,
                             granularity=granularity, # 'M30' in this case
                             dailyAlignment=config.OANDA_API['dailyAlignment'],
                             alignmentTimezone=config.OANDA_API['alignmentTimezone'])

            oanda.run(start=cstart.isoformat(),
                      end=cend.isoformat(),
                      roll=True)

            candle_list = oanda.fetch_candleset()
            for c in candle_list:
                if c.lowAsk <= self.price <= c.highAsk:
                    return c.time
        else:
            return 'n.a.'

    def inarea_bounces(self, plist, part='closeAsk'):
        '''
        Function to identify the candles for which price is in the area defined
        by self.upper and self.lower

        Parameters
        ----------
        plist: PivotList
               Containing the PivotList for bounces (including the ones
                 that are not in HRarea)
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        list with bounces that are in the area and will also initialize the
        'bounces' member class
        '''

        # get bounces in the horizontal area
        carray=np.array(plist.clist.clist)
        bounces=carray[np.logical_or(plist.plist == 1, plist.plist == -1)]

        ix=0
        in_area_list = []
        for c in bounces:
            price = getattr(c, part)
            if price >= self.lower and price <= self.upper:
                in_area_list.append(c)
            ix+=1

        self.bounces=in_area_list

        return in_area_list
