import pdb
import warnings

from Pattern.Counter import Counter
from OandaAPI import OandaAPI
import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt
import datetime


class CounterDbTp(Counter):
    '''
    This class represents a trade showing Counter doubletop pattern (inherits from Counter)

    Class variables
    ---------------

    id : str, Required
         Id used for this trade
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
    diff : float. Optional
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
    period_dbounce: int, Optional
                    Number of candles for period starting in self.start that will contain the double bounce
                    characteristic of this pattern. Default: 150
    period1st_bounce: int, Optional
                      Controls the maximum number of candles allowed between
                      self.start and the location of the most recent bounce.
                      Default:10

    '''

    def __init__(self, pair, start, HR_pips=30, threshold=0.50, min_dist=5, period_dbounce=150,
                 period1st_bounce=10,**kwargs):

        self.start = start
        self.HR_pips = HR_pips
        self.threshold = threshold
        self.min_dist = min_dist
        self.period_dbounce = period_dbounce
        self.period1st_bounce = period1st_bounce

        allowed_keys = ['id','timeframe','entry','period', 'trend_i', 'type', 'SL',
                        'TP', 'SR', 'RR']
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        super().__init__(pair)

        # Initialise the private class attributes containing some pattern restrictions
        delta_period = None
        delta_from_start = None
        if self.timeframe == "D":
            delta_period = datetime.timedelta(hours=24 * self.period_dbounce)
            delta_from_start = datetime.timedelta(hours=24 * self.period1st_bounce)
        else:
            fgran = self.timeframe.replace('H', '')
            delta_period = datetime.timedelta(hours=int(fgran) * self.period_dbounce)
            delta_from_start = datetime.timedelta(hours=int(fgran) * self.period1st_bounce)

        # timepoint cutoff that defines the period for which the doubletop will be looked for
        self.__period_dbounce_point = self.start - delta_period
        # timepoint cutoff that the defines the period from which the first bounce needs to be
        # located
        self.__period1st_bounce_point = self.start - delta_from_start

    def __get_candles4timedelta(self,t):
        '''
        This private function takes a datetime.timedelta
        and returns the equivalent number of candles

        Parameters
        ----------
        t : Datetime.timedelta

        Returns
        -------
        int : representing the number of candles
        '''

        days_in_hours=t.days*24
        secs_in_hours=t.seconds/3600
        total_hours=days_in_hours+secs_in_hours

        no_candles=None
        if self.timeframe == "D":
            no_candles=(total_hours/24)
        else:
            hours = int(self.timeframe.replace('H', ''))
            no_candles=(total_hours/hours)

        return no_candles



    def __validate_bounces(self,min_len=2, distance_cutoff=5):
        '''
        Private function to validate bounces identified by self.get_bounces

        Parameters
        ----------
        min_len: int
                 Minimum number of bounces required to validate. Default: 2
        distance_cutoff: int
                         Minimum number of candles between 1st and 2nd bounce
                         Default: 5

        Returns
        -------
        bool: True if it validates, False otherwise
        '''

        if len(self.bounces) < min_len:
            warnings.warn("Less than 2 bounces identified")
            return False

        if self.bounces[-1][0] < self.__period1st_bounce_point:
            warnings.warn("First identified bounce is before the time cutoff")
            return False

        diff = self.bounces[-1][0] - self.bounces[-2][0]
        candles=self.__get_candles4timedelta(diff)
        if candles<=distance_cutoff:
            return False

        return True

    def get_bounces(self, plot=False, part='closeAsk'):
        '''
        Function to identify all bounces

        Parameters
        ----------
        plot: bool
              If true, then produce a plot displaying
              the location of the bounces. Default: false
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        It will set the self.bounces attribute
        '''

        min_dist_res = 10
        HR_pips_res=100
        # relax parameters to detect first and second bounces
        self.set_bounces(part=part, HR_pips=self.HR_pips, threshold=self.threshold, min_dist=self.min_dist,min_dist_res=min_dist_res,
                         start= self.__period_dbounce_point)

        # Will check if there are at least 2 bounces within 'period' or there are a maximum of period_first_bounce
        # candles between self.start and self.bounces[-1], if not then it will try iteratively decreasing
        # first the threshold, then the min_dist_res and finally the HR_pips
        threshold_res = 0.5
        while (self.__validate_bounces() is False) and (threshold_res > 0.0):
            threshold_res -= 0.1
            warnings.warn("Less than 2 bounces identified or last bounce is not correct. "
                          " Will try with 'threshold_res'={0}".format(threshold_res))
            self.set_bounces(part=part, HR_pips=self.HR_pips, threshold=threshold_res, min_dist=5, min_dist_res=10,
                             start=self.__period_dbounce_point)

        while (self.__validate_bounces() is False) and (min_dist_res > 1):
            min_dist_res -= 1
            warnings.warn("Less than 2 bounces identified or last bounce is not correct. "
                          " Will try with 'min_dist_res'={0}".format(min_dist_res))
            self.set_bounces(part=part, HR_pips=self.HR_pips, threshold=self.threshold, min_dist=1, min_dist_res=min_dist_res,
                             start=self.__period_dbounce_point)

        while (self.__validate_bounces() is False) and (HR_pips_res <= 200):
            HR_pips_res += 5
            warnings.warn("Less than 2 bounces identified or last bounce is not correct. "
                          " Will try with 'HR_pips_res'={0}".format(HR_pips_res))
            self.set_bounces(part=part, HR_pips=HR_pips_res, threshold=self.threshold, min_dist=1, min_dist_res=10,
                             start=self.__period_dbounce_point)

        # Finally, and as a last-ditch effort, combine the decrease of threshold and min_dist
        threshold_res=0.5
        while (self.__validate_bounces() is False) and (threshold_res > 0.0):
            threshold_res -= 0.1
            min_dist_res = 10
            warnings.warn("Less than 2 bounces identified or last bounce is not correct."
                          " Will try with 'threshold_res'={0}".format(threshold_res))

            self.set_bounces(part=part, HR_pips=self.HR_pips, threshold=threshold_res, min_dist=5, min_dist_res=10,
                             start=self.__period_dbounce_point)

            while (self.__validate_bounces() is False) and (min_dist_res > 1):
                min_dist_res -= 1
                warnings.warn("Less than 2 bounces identified or last bounce is not correct. "
                              " Will try with 'min_dist_res'={0}".format(min_dist_res))
                self.set_bounces(part=part, HR_pips=self.HR_pips, threshold=threshold_res, min_dist=1,
                                 min_dist_res=min_dist_res,start=self.__period_dbounce_point)

        pdb.set_trace()
        if self.__validate_bounces() is False:
            raise Exception("Less than 2 bounces were found for this trade."
                            "Perphaps you can try to run peakutils with lower threshold "
                            "or min_dist parameters")

        final_bounces = [self.bounces[-2], self.bounces[-1]]

        # check bounces from the second bounce with a stricter parameter set
        self.set_bounces(part=part, HR_pips=60, threshold=0.5, min_dist=5, min_dist_res=5,
                         end=self.bounces[-2][0])

        if self.bounces is not None:
            # append the self.bounces at the beginning of final_bounces
            final_bounces[0:0] = self.bounces

        self.bounces = final_bounces

        if plot is True:

            prices = []
            datetimes = []
            for c in self.clist_period.clist:
                prices.append(getattr(c, part))
                datetimes.append(c.time)

            fig = plt.figure(figsize=(20, 10))
            ax = plt.axes()
            ax.plot(datetimes, prices, color="black")

            for b in final_bounces:
                dt=b[0]
                ix=datetimes.index(dt)
                plt.scatter(datetimes[ix], prices[ix], s=50)

            outfile = "{0}.png".format(self.id)

            fig.savefig(outfile, format='png')

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

        # now check rsi for this bounce
        candle = self.clist_period.fetch_by_time(self.bounce_1st[0])

        isonrsi = False

        if candle.rsi >= 70 or candle.rsi <= 30:
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

        self.bounce_2nd=self.bounces[-1]

        # now check rsi for this bounce
        candle = self.clist_period.fetch_by_time(self.bounce_2nd[0])

        isonrsi = False

        if candle.rsi >= 70 or candle.rsi <= 30:
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

        self.set_lasttime()
        self.set_entry_onrsi()
        self.get_bounces(plot=True)
        self.set_1stbounce()
        self.set_2ndbounce()
        self.bounces_fromlasttime()
        self.set_diff()
        self.set_valley()

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
            period=1000,
            SR=self.SR,
            SL=self.SL,
            TP=self.TP,
            trend_i=str(self.trend_i))

        c.init_feats()

        self.slope=c.slope
        self.n_rsibounces = c.n_rsibounces
        self.rsibounces_lengths=c.rsibounces_lengths
        self.divergence=c.divergence
        self.length_candles=c.length_candles
        self.length_pips=c.length_pips

        warnings.warn("[INFO] Done init_trend_feats")

    def set_diff(self):
        '''
        Function to calculate the diff between rsi_1st & rsi_2nd

        Returns
        -------
        It will set the 'diff' attribute of the class
        '''

        rsi1st_val = self.clist_period.fetch_by_time(self.bounce_1st[0]).rsi
        rsi2nd_val = self.clist_period.fetch_by_time(self.bounce_2nd[0]).rsi

        self.diff=rsi1st_val-rsi2nd_val

    def set_valley(self):
        '''
        Function to calculate the length of the valley
        between bounce_1st & bounce_2nd

        Returns
        -------
        It will set the 'valley' attribute of the class
        '''

        oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone='Europe/London',
                         dailyAlignment=22)

        oanda.run(start=self.bounce_1st[0].isoformat(),
                  end=self.bounce_2nd[0].isoformat())

        candle_list = oanda.fetch_candleset()

        self.valley=len(candle_list)