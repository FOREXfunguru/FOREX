import pdb
import datetime
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
    period: int, Optional
            Period that will be checked back in time. Units used will be the ones dictated by self.timeframe.
            Default : 1000
    trend_i: datetime, Optional
             start of the trend
    type: str, Optional
          What is the type of the trade (long,short)
    SL:  float, Optional
         Stop/Loss price
    TP:  float, Optional
         Take profit price
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
               datetime for last time that price has been above/below self.SR
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
    '''

    def __init__(self,
                 start,
                 pair,
                 timeframe,
                 period=1000,
                 trend_i=None,
                 type=None,
                 SL=None,
                 TP=None,
                 SR=None,
                 bounces=None,
                 clist_period=None,
                 clist_trend=None,
                 last_time=None,
                 bounces_lasttime=None,
                 slope=None,
                 n_rsibounces=None,
                 rsibounces_lengths=None,
                 divergence=None
                 ):
        self.start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        self.pair = pair
        self.timeframe = timeframe
        self.period = period
        self.trend_i = datetime.datetime.strptime(trend_i, '%Y-%m-%d %H:%M:%S')
        self.type = type
        self.SL = SL
        self.TP = TP
        self.SR = SR
        self.bounces = bounces
        self.clist_period = clist_period
        self.clist_trend = clist_trend
        self.last_time = last_time
        self.bounces_lasttime = bounces_lasttime
        self.slope = slope
        self.n_rsibounces=n_rsibounces
        self.rsibounces_lengths= rsibounces_lengths
        self.divergence=divergence

        self.__init_clist_period()
        self.__init_clist_trend()

    def __init_clist_trend(self):
        '''
        Private function to initialise self.clist_trend class attribute
        '''

        # checking for feats in trend before 1st bounce
        oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone='Europe/London',
                         dailyAlignment=22,
                         start=self.trend_i.isoformat(),
                         end=self.start.isoformat())

        candle_list = oanda.fetch_candleset()

        cl = CandleList(candle_list, self.pair, granularity=self.timeframe)

        cl.calc_rsi(period=self.period)

        self.clist_trend = cl


    def __init_clist_period(self):
        '''
        Private function to initialise self.clist_period class attribute
        '''

        delta = None
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
                         dailyAlignment=22,
                         start=start.isoformat(),
                         end=end.isoformat())

        candle_list = oanda.fetch_candleset()

        cl = CandleList(candle_list, self.pair, granularity=self.timeframe)

        cl.calc_rsi(period=self.period)

        self.clist_period = cl


    def set_bounces(self):
        '''
        Function to calculate previous bounces at self.SR

        Returns
        -------
        Will set the class 'bounces' attribute
        '''

        close_prices = []
        datetimes = []
        for c in self.clist_period:
            close_prices.append(c.closeAsk)
            datetimes.append(c.time)

        resist = HArea(price=self.SR, pips=50, instrument=self.pair, granularity=self.timeframe)

        (bounces, outfile) = resist.number_bounces(datetimes=datetimes,
                                                   prices=close_prices,
                                                   min_dist=5)

        self.bounces=bounces

    def set_lasttime(self):
        '''
        Function to set the datetime for last time that price has been above/below self.SR

        Returns
        -------
        Will set the class 'last_time' attribute representing the last time the price was above/below the self.SR
        'last_time' will be set to 01/01/1900 if not defined for self.period
        '''

        resist = HArea(price=self.SR, pips=50, instrument=self.pair, granularity=self.timeframe)

        if self.type == "short": position = 'above'
        if self.type == "long": position = 'below'

        last_time=None

        last_time = resist.last_time(clist=self.clist_period, position=position)

        if last_time is None:
            last_time=datetime.datetime(1900, 1, 1)

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

    def set_slope(self):
        '''
        Function to set the slope for trend conducting to entry

        Returns
        -------
        Will set the slope class attribute and also the type attribute
        in self.clist_trend CandleList
        '''


        (model, outfile) = self.clist_trend.fit_reg_line()

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