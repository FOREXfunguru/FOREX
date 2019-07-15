import pdb
import warnings

import matplotlib
from Pattern.counter import Counter
from oanda_api import OandaAPI

matplotlib.use('PS')
import matplotlib.pyplot as plt
import datetime
import config
import numpy as np
from utils import *
from candlelist import CandleList

class CounterDbTp(Counter):
    '''
    This class represents a trade showing Counter doubletop pattern (inherits from Counter)

    Class variables
    ---------------

    id : str, Required
         Id used for this object
    start: datetime, Required
           Time/date when the trade was taken. i.e. 20-03-2017 08:20:00s
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    entry: float, Optional
           entry price
    trend_i: datetime, Required
             start of the trend
    type: str, Optional
          What is the type of the trade (long,short)
    SL:  float, Optional
         Stop/Loss price
    TP:  float, Optional
         Take profit price
    SR:  float, Optional
         Support/Resistance area
    bounce_1st : with tuple (datetime,price) containing the datetime
                 and price for this bounce
    bounce_2nd : with tuple (datetime,price) containing the datetime
                 and price for this bounce
    rsi_1st : bool, Optional
              Is price in overbought/oversold
              area in first peak
    rsi_2nd : bool, Optional
              Is price in overbought/oversold
              area in second peak
    diff : int. Optional
            Variable containing the absolute (no sign) difference (in pips)
    diff_rsi : float. Optional
               Variable containing the difference between rsi_1st and rsi_2nd
    valley : int Optional
             Length in number of candles between  bounce_1st and bounce_2nd
    n_rsibounces : int, Optional
                  Number of rsi bounces for trend conducting to 1st bounce
    slope: float, Optional
           Float with the slope of trend conducting to 1st bounce
    HR_pips: int, Optional
             Number of pips over/below S/R used for trying to identify bounces
             Default: 200
    threshold: float Optional
               Threshold for detecting peaks. Default : 0.50
    min_dist: int, Optional
              Minimum distance between peaks. Default : 5
    period: int, Optional
            number of candles from self.start that will be considered in order to
            to look for peaks/valleys
    period1st_bounce: int, Optional
                      Controls the maximum number of candles allowed between
                      self.start and the location of the most recent bounce.
                      Default:10
    clist_period : CandleList
                   CandleList that goes from self.start to self.period.
                   It will be initialised by __initclist

    '''

    def __init__(self, pair, start, HR_pips=200, threshold=0.50, min_dist=5,
                 period1st_bounce=10, **kwargs):

        # get values from config file
        if 'HR_pips' in config.CTDBT: HR_pips = config.CTDBT['HR_pips']
        if 'threshold' in config.CTDBT: threshold = config.CTDBT['threshold']
        if 'min_dist' in config.CTDBT: min_dist = config.CTDBT['min_dist']
        if 'period1st_bounce' in config.CTDBT: period1st_bounce = config.CTDBT['period1st_bounce']
        if 'period' in config.CTDBT: period = config.CTDBT['period']

        self.pair = pair
        self.start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        self.HR_pips = HR_pips
        self.threshold = threshold
        self.min_dist = min_dist
        self.period1st_bounce = period1st_bounce
        self.period = period

        allowed_keys = ['id', 'timeframe', 'entry', 'period', 'trend_i', 'type', 'SL',
                        'TP', 'SR', 'RR']

        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)

        # timepoint cutoff that the defines the period from which the first bounce needs to be
        # located
        self.__period1st_bounce_point = self.__get_time4candles(n=self.period1st_bounce,
                                                                anchor_point=self.start)
        # init the CandleList from self.period to self.start
        self.__initclist()
        self.init_feats()

    def __get_time4candles(self, n, anchor_point):
        '''
        This private function takes a a number of candles
        and returns a Datetime corresponding to
        this number of candles

        Parameters
        ----------
        n : int
            Number of candles
        anchor_point : datetime
            Datetime used as the anchor for calculation

        Returns
        -------
        Datetime.datetime
        '''

        # Initialise the private class attributes containing some pattern restrictions
        delta_from_start = None
        delta_one = None
        if self.timeframe == "D":
            delta_from_start = datetime.timedelta(hours=24 * n)
            delta_one = datetime.timedelta(hours=24)
        else:
            fgran = self.timeframe.replace('H', '')
            delta_from_start = datetime.timedelta(hours=int(fgran) * n)
            delta_one = datetime.timedelta(hours=int(fgran))

        # calculate the cutoff for the first threshold using the number of candles
        oanda = OandaAPI(url=config.OANDA_API['url'],
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone=config.OANDA_API['alignmentTimezone'],
                         dailyAlignment=config.OANDA_API['dailyAlignment'])

        start = anchor_point - delta_from_start
        end = anchor_point.isoformat()

        oanda.run(start=start.isoformat(),
                  end=end,
                  roll=True)

        candle_list = oanda.fetch_candleset()

        while len(candle_list) < n:
            start = start - delta_one
            oanda.run(start=start.isoformat(),
                      end=end,
                      roll=True)
            candle_list = oanda.fetch_candleset()

        return start

    def __validate1stbounce(self):
        '''
        Private function to validate the first bounce identified by self.get_first_bounce

        Returns
        -------
        str: Reason for not validating
             'NO_BOUNCE': The bounce was not found
             'TOO_MANY': Too many bounces found
             'OK': Ok
        '''

        if len(self.bounces) < 1:
            warnings.warn("Not enough bounces")
            return (False, 'NO_BOUNCE')
        elif len(self.bounces) > 1:
            warnings.warn("Too many bounces")
            return (False, 'TOO_MANY')
        else:
            return (True, 'OK')

    def __validate2ndbounce(self):
        '''
        Private function to validate the second bounce identified by self.get_second_bounce

        Returns
        -------
        str: Reason for not validating
             'NO_BOUNCE': The bounce was not found
             'OK': Ok
        '''

        if len(self.bounces) < 1:
            warnings.warn("Not enough bounces")
            return (False, 'NO_BOUNCE')
        else:
            return (True, 'OK')

    def __initclist(self):
        '''
        Private function to initialize the CandleList object that goes from self.start
        to self.period

        This will set the self.clist_period class attribute
        '''

        delta_period=periodToDelta(self.period, self.timeframe)
        delta_1=periodToDelta(1, self.timeframe)
        start = self.start - delta_period # get the start datetime for this CandleList period
        end = self.start + delta_1 # increase self.start by one candle to include self.start

        oanda = OandaAPI(url=config.OANDA_API['url'],
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone=config.OANDA_API['alignmentTimezone'],
                         dailyAlignment=config.OANDA_API['dailyAlignment'])

        oanda.run(start=start.isoformat(),
                  end=end.isoformat(),
                  roll=True
                  )

        candle_list = oanda.fetch_candleset(vol_cutoff=0)

        cl = CandleList(candle_list, self.pair, granularity=self.timeframe, id=self.id)

        self.clist_period=cl

    def __inarea_bounces(self, bounces, HRpips, part='closeAsk'):
        '''
        Function to identify the candles for which price is in the area defined
        by self.SR+HRpips and self.SR-HRpips

        Parameters
        ----------
        bounces: list
                 Containing the initial list of candles
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        list with bounces that are in the area
        '''
        # get bounces in the horizontal area
        lower = substract_pips2price(self.pair, self.SR, HRpips)
        upper = add_pips2price(self.pair, self.SR, HRpips)

        in_area_list = []
        for c in bounces:
            price = getattr(c, part)
          #  print("u:{0}-l:{1}|p:{2}".format(upper, lower, price))
            if price >= lower and price <= upper:
                in_area_list.append(c)

        return in_area_list

    def get_first_bounce(self, part='closeAsk'):
        '''
        Function that uses the the Zigzag algorithm to identify the first bounce (most recent)
        of the CounterDoubleTop pattern

        Parameters
        ----------
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        It will set the self.bounces attribute
        '''

        # get sliced CandleList from datetime defined by self.period1st_bounce period
        start_clist=self.clist_period.slice(start=self.__period1st_bounce_point)

        outfile="{0}/{1}.fstbounce.png".format(config.PNGFILES['bounces'],self.id.replace(' ', '_'))
        bounces=start_clist.get_pivots(outfile, th_up=0.00, th_down=-0.00)

        arr = np.array(start_clist.clist)

        # consider type of trade in order to select peaks or valleys
        if self.type=='short':
            bounce_candles = arr[bounces==1]
        elif self.type=='long':
            bounce_candles = arr[bounces==-1]

        in_area_list=self.__inarea_bounces(bounce_candles,self.HR_pips)

        HRpips=self.HR_pips
        while len(in_area_list)==0 and HRpips<=config.CTDBT['max_HRpips']:
            HRpips=HRpips+config.CTDBT['step_pips']
            in_area_list = self.__inarea_bounces(bounce_candles, HRpips)

        # keep running the improve_resolution function until a single bounce is obtained
        while len(in_area_list)>1:
            inarea_cl = CandleList(in_area_list, instrument=self.pair, granularity=self.timeframe)
            in_area_list=inarea_cl.improve_resolution(price=self.SR)

        assert len(in_area_list)==1, "Exactly one single bounce is needed"

        self.bounce_1st=in_area_list[0]

    def set_1stbounce(self):
        '''
        Function to set bounce_1st (the one that is before the most recent)
        and rsi_1st class attributes

        Returns
        -------
        Nothing
        '''

        self.bounce_1st = self.bounces[-2]
        if self.trend_i > self.bounce_1st[0]:
            raise Exception("Error in the definition of the 1st bounce, it is older than the trend_start."
                            "Perphaps you can try to run peakutils with lower threshold or min_dist "
                            "parameters")

        # now check rsi for this bounce and some candles before/after the bounce
        candles = self.clist_period.fetch_by_time(self.bounce_1st[0], period=4)

        isonrsi = False
        for c in candles:
            if c.rsi >= 70 or c.rsi <= 30:
                isonrsi = True

        self.rsi_1st = isonrsi

    def set_2ndbounce(self):
        '''
        Function to set bounce_2nd (the one that is the most recent)
        and rsi_2nd class attributes
        Returns
        -------
        Nothing
        '''

        self.bounce_2nd = self.bounces[-1]

        # now check rsi for this bounce and some candles before/after the bounce
        candles = self.clist_period.fetch_by_time(self.bounce_2nd[0], period=4)

        isonrsi = False

        for c in candles:
            if c.rsi >= 70 or c.rsi <= 30:
                isonrsi = True

        self.rsi_2nd = isonrsi

    def init_feats(self):
        '''
        Function to initialise all object features

        Returns
        -------
        It will initialise all object's features
        '''

        warnings.warn("[INFO] Run init_feats")

        self.get_first_bounce()
       # self.set_lasttime()
       # self.set_entry_onrsi()
       # self.set_1stbounce()
       # self.set_2ndbounce()
       # self.bounces_fromlasttime()
       # self.set_diff()
       # self.set_diff_rsi()
       # self.set_valley()

        warnings.warn("[INFO] Done init_feats")

    def init_trend_feats(self):
        '''
        Function to initialize the features for
        trend going from 'trend_i' to 'bounce_1st'

        Returns
        -------
        Nothing
        '''

        warnings.warn("[INFO] Run init_trend_feats")

        c = Counter(
            start=str(self.bounce_1st[0]),
            pair=self.pair,
            timeframe=self.timeframe,
            type=self.type,
            SR=self.SR,
            SL=self.SL,
            TP=self.TP,
            trend_i=str(self.trend_i),
            id=self.id)

        c.init_feats()

        pdb.set_trace()

        self.slope = c.slope
        self.n_rsibounces = c.n_rsibounces
        self.rsibounces_lengths = c.rsibounces_lengths
        self.divergence = c.divergence
        self.length_candles = c.length_candles
        self.length_pips = c.length_pips

        warnings.warn("[INFO] Done init_trend_feats")

    def set_diff(self):
        '''
        Function to calculate the diff between rsi_1st & rsi_2nd

        Returns
        -------
        It will set the 'diff' attribute of the class and calculate
        the number of pips from the difference. The sign will be ignored
        and the absolute number of pips is returned
        '''

        diff = self.bounce_1st[1] - self.bounce_2nd[1]

        (first, second) = self.pair.split("_")
        if first == 'JPY' or second == 'JPY':
            diff = diff * 100
        else:
            diff = diff * 10000

        self.diff = abs(round(diff))

    def set_diff_rsi(self):
        '''
        Function to calculate the diff between rsi_1st & rsi_2nd

        Returns
        -------
        It will set the 'diff_rsi' attribute of the class
        '''

        rsi1st_val = self.clist_period.fetch_by_time(self.bounce_1st[0]).rsi
        rsi2nd_val = self.clist_period.fetch_by_time(self.bounce_2nd[0]).rsi

        self.diff_rsi = rsi1st_val - rsi2nd_val

    def set_valley(self):
        '''
        Function to calculate the length of the valley
        between bounce_1st & bounce_2nd

        Returns
        -------
        It will set the 'valley' attribute of the class
        '''

        oanda = OandaAPI(url=config.OANDA_API['url'],
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone=config.OANDA_API['alignmentTimezone'],
                         dailyAlignment=config.OANDA_API['dailyAlignment'])

        oanda.run(start=self.bounce_1st[0].isoformat(),
                  end=self.bounce_2nd[0].isoformat())

        candle_list = oanda.fetch_candleset(vol_cutoff=0)

        self.valley = len(candle_list)
