import pdb
import datetime
import warnings
from OandaAPI import OandaAPI
from CandleList import CandleList
from HArea import HArea

class Counter(object):
    '''
    This class represents a trade showing Counter pattern

    Class variables
    ---------------

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
    period: int, Optional
            Period that will be checked back in time. Units used will be the ones dictated by self.timeframe.
            Default : 1000
    type: str, Optional
          What is the type of the trade (long,short)
    SL:  float, Optional
         Stop/Loss price
    TP:  float, Optional
         Take profit price
    RR:  float, Optional
         Risk ratio of the trade
    SR:  float, Optional
         Support/Resistance area
    bounces: list, Optional
             List with tuples [(datetime,price)] containing the datetime
             and price for different bounces
    clist_period: CandleList, Optional
                  Candlelist extending back (defined by 'period') in time since the start of the pattern
    clist_trend: CandleList, Optional
                 CandleList extending back to datetime defined by self.trend_i
    last_time: datetime object, Optional
               datetime for last time that price has been above/below self.SR. If last_time is not found before
               the start of the historical record then it will be set to '01/01/1900 00:00:00'
    bounces_lasttime: list, Optional
                      List with tuples [(datetime,price)] containing the datetime
                      and price for different bounces after the lasttime
    slope: float, Optional
           Float with the slope of trend conducting to entry
    n_rsibounces: int, Optional
                  Number of rsi bounces for trend conducting to start
    rsibounces_lengths: list, Optional
                        List with lengths for each rsi bounce
    divergence: bool, Optional
                True is there is RSI divergence
    entry_onrsi: bool, Optional
                 Is entry candle on rsi territory
    length_candles: int, Optional
                    Number of candles in self.clist_trend
    length_pips: int, Optional
                 Length in number of pips for self.clist_trend
    '''

    def __init__(self, pair, period= 3000, **kwargs):

        allowed_keys = [ 'start','timeframe','period','entry','trend_i', 'type', 'SL',
                        'TP','SR','RR','bounces','clist_period','clist_trend','last_time',
                        'bounces_lasttime','slope','n_rsibounces','rsibounces_lengths',
                        'divergence','entry_onrsi','length_candles','length_pips']

        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        self.pair=pair
        self.period=period
        self.start = datetime.datetime.strptime(self.start, '%Y-%m-%d %H:%M:%S')
        self.__init_clist_period()

        if not hasattr(self, 'TP'):
            if not hasattr(self, 'RR'): raise Exception("Neither the RR not the TP is defined. Please provide RR")
            diff=(self.entry-self.SL)*self.RR
            self.TP=round(self.entry+diff,4)

        if hasattr(self, 'trend_i'):
            self.trend_i = datetime.datetime.strptime(self.trend_i, '%Y-%m-%d %H:%M:%S')
        else:
            self.calc_itrend()
        self.__init_clist_trend()

    def __init_clist_trend(self):
        '''
        Private function to initialise self.clist_trend class attribute

        This function process the candlelist going from self.trend_i to self.start
        '''

        warnings.warn("[INFO] Run __init_clist_trend")

            # checking for feats in trend before 1st bounce
        oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone='Europe/London',
                         dailyAlignment=22)

        oanda.run(start=self.trend_i.isoformat(),
                  end=self.start.isoformat())

        candle_list = oanda.fetch_candleset(vol_cutoff=0)

        cl = CandleList(candle_list, self.pair, granularity=self.timeframe)

        warnings.warn("[INFO] Run cl.calc_rsi")

        cl.calc_rsi()

        warnings.warn("[INFO] Done cl.calc_rsi")

        self.clist_trend = cl


    def __init_clist_period(self):
        '''
        Private function to initialise self.clist_period class attribute

        This function process the candlelist going from self.start-self.period to
        self.start
        '''

        warnings.warn("[INFO] Run __init_clist_period")

        delta_period = None
        delta_1 = None
        if self.timeframe == "D":
            delta_period = datetime.timedelta(hours=24 * self.period)
            delta_1 = datetime.timedelta(hours=24)
        else:
            fgran = self.timeframe.replace('H', '')
            delta_period = datetime.timedelta(hours=int(fgran) * self.period)
            delta_1 = datetime.timedelta(hours=int(fgran))

        start = self.start - delta_period
        end = self.start + delta_1

        oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone='Europe/London',
                         dailyAlignment=22)

        oanda.run(start=start.isoformat(),
                  end=end.isoformat(),
                  roll=True
                  )

        candle_list = oanda.fetch_candleset(vol_cutoff=0)

        cl = CandleList(candle_list, self.pair, granularity=self.timeframe)

        warnings.warn("[INFO] Run cl.calc_rsi")

        cl.calc_rsi()

        warnings.warn("[INFO] Done cl.calc_rsi")

        self.clist_period = cl


    def init_feats(self):
        '''
        Function to initialise all object features

        Returns
        -------
        It will initialise all object's features
        '''

        self.set_bounces()
        self.set_lasttime()
        self.bounces_fromlasttime()
        self.set_slope()
        self.set_rsibounces_feats()
        self.set_divergence()
        self.set_entry_onrsi()
        self.set_length_candles()
        self.set_length_pips()

    def calc_itrend(self):
        '''
        Function to calculate the datetime for the start of the trend conducting to entry
        The start of the trend will be defined by the first time the price is on RSI on the
        other end of the RSI spectrum, i.e. if the trade type if short it will look for the
        first time the price rsi is <=30. If the trade type is long, it will look for the
        price rsi >=70

        Returns
        -------
        Will set the class 'trend_i' attribute and will return the datetime for this 'trend_i'
        '''

        for c in reversed(self.clist_period.clist):
            if self.type == 'long' and c.rsi>=70:
                self.trend_i=c.time
                return c.time
            elif self.type == 'short' and c.rsi<=30:
                self.trend_i = c.time
                return c.time

    def set_bounces(self, part='closeAsk',HR_pips=50, threshold=0.50,
                    start=None, end=None, min_dist=10,min_dist_res=10):
        '''
        Function to calculate previous bounces at self.SR

        Parameters
        ----------
        part: str
              Candle part used for the calculation. Default='closeAsk'
        HR_pips: int
              Number of pips around self.SR to extend the area. Default=50
        threshold: float
                   Threshold for detecting peaks. Default : 0.50
        start: datetime
               Identify bounces only from this start datetime
        end: datetime
             Do not identify bounces from this datetime
        min_dist: int
                  Minimum distance to detect bounces. Default : 10

        Returns
        -------
        Will set the class 'bounces' attribute
        '''

        prices = []
        datetimes = []
        for c in self.clist_period.clist:
            prices.append(getattr(c, part))
            datetimes.append(c.time)

        resist = HArea(price=self.SR, pips=HR_pips, instrument=self.pair, granularity=self.timeframe)

        if hasattr(self, 'id'):
            bounces = resist.get_bounces(datetimes=datetimes,
                                         prices=prices,
                                         threshold=threshold,
                                         type=self.type,
                                         min_dist=min_dist,
                                         min_dist_res=min_dist_res)
        else:
            bounces = resist.get_bounces(datetimes=datetimes,
                                         prices=prices,
                                         threshold=threshold,
                                         type=self.type,
                                         min_dist=min_dist,
                                         min_dist_res=min_dist_res)

        bounces_new=[]
        if start is None and end is not None:
            bounces_new = [d for d in bounces if d[0]<end]
            if len(bounces_new)>1:
                self.bounces=bounces_new
            else:
                self.bounces=None

        if start is not None and end is None:
            bounces_new = [d for d in bounces if d[0] >= start]
            if len(bounces_new) >0:
                self.bounces = bounces_new
            else:
                self.bounces = []

        if start is not None and end is not None:
            bounces_new = [d for d in bounces if d[0] >= start and d[0] <=end ]
            if len(bounces_new) >0:
                self.bounces = bounces_new
            else:
                self.bounces =[]

        if start is None and end is None:
            self.bounces=bounces

    def set_lasttime(self):
        '''
        Function to set the datetime for last time that price has been above/below self.SR

        Returns
        -------
        Will set the class 'last_time' attribute representing the last time the price was above/below the self.SR
        'last_time' will be set to the datetime for the first candle in self.clist_period if last time was not found
        '''

        resist = HArea(price=self.SR, pips=50, instrument=self.pair, granularity=self.timeframe)

        if self.type == "short": position = 'above'
        if self.type == "long": position = 'below'

        last_time=None

        last_time = resist.last_time(clist=self.clist_period, position=position)

        if last_time is None:
            last_time=self.clist_period.clist[0].time

        self.last_time=last_time

    def bounces_fromlasttime(self):
        '''
        Function to get the bounces occurring after last_time

        Returns
        -------
        Will set the bounces_lasttime class attribute
        '''

        bounces = [n for n in self.bounces if n[0] >= self.last_time]

        self.bounces_lasttime=bounces

    def set_slope(self,k_perc=None):
        '''
        Function to set the slope for trend conducting to entry

        Parameters
        ----------
        k_perc : int
                % of CandleList length that will be used as window size used for calculating the rolling average.
                For example, if CandleList length = 20 Candles. Then the k=25% will be a window_size of 5
                Default: None

        Returns
        -------
        Will set the slope class attribute and also the type attribute
        in self.clist_trend CandleList
        '''

        if k_perc is not None:
            (model, outfile, mse) = self.clist_trend.fit_reg_line(k_perc=k_perc)
        else:
            (model, outfile, mse) = self.clist_trend.fit_reg_line()

        self.slope=model.coef_[0, 0]

        if model.coef_[0,0]>0:
            self.clist_trend.type='long'
        elif model.coef_[0,0]<0:
            self.clist_trend.type='short'


    def set_rsibounces_feats(self):
        '''
        Function to set the n_rsibounces and rsibounces_lengths
        for trend conducting to entry

        Returns
        -------
        Will set the n_rsibounces and rsibounces_lengths
        class attributes
        '''

        dict1 = self.clist_trend.calc_rsi_bounces()

        self.n_rsibounces=dict1['number']
        self.rsibounces_lengths=dict1['lengths']

    def set_divergence(self):
        '''
        Function to check if there is divergence involving the RSI indicator
        for trend conducting to entry

        Returns
        -------
        Will set the divergence class attribute
        '''

        direction = None
        if self.slope > 0:
            direction = 'up'
        else:
            direction = 'down'

        res=self.clist_trend.check_if_divergence(direction=direction)

        self.divergence=res

    def set_entry_onrsi(self):
        '''
        Function to check if entry candle is on rsi territory

        Returns
        -------
        Will set the entry_onrsi class attribute
        '''

        entry_c=self.clist_period.fetch_by_time(self.start)

        isonrsi=False

        if entry_c.rsi>=70 or entry_c.rsi<=30:
            isonrsi=True

        self.entry_onrsi=isonrsi

    def set_length_candles(self):
        '''
        Function to get the length in number of candles
        for self.clist_trend

        Returns
        -------
        Will set the length_candles class attribute
        '''

        self.length_candles=self.clist_trend.get_length_candles()

    def set_length_pips(self):
        '''
        Function to get the length in number of candles
        for self.clist_trend

        Returns
        -------
        Will set the length_pips class attribute
        '''

        self.length_pips = self.clist_trend.get_length_pips()

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
