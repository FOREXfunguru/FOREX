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
    period1st_bounce: int, Optional
                      Controls the maximum number of candles allowed between
                      self.start and the location of the most recent bounce.
                      Default:10

    '''

    def __init__(self, pair, start, HR_pips=30, threshold=0.50, min_dist=5,
                 period1st_bounce=8,**kwargs):

        self.start = start
        self.HR_pips = HR_pips
        self.threshold = threshold
        self.min_dist = min_dist
        self.period1st_bounce = period1st_bounce

        allowed_keys = ['id','timeframe','entry','period', 'trend_i', 'type', 'SL',
                        'TP', 'SR', 'RR']

        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)

        # initialize the Counter object that will go from self.start to self.start-period
        super().__init__(pair,period=4500)

        # timepoint cutoff that the defines the period from which the first bounce needs to be
        # located
        self.__period1st_bounce_point = self.__get_time4candles(n=self.period1st_bounce, anchor_point=self.start )

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
            delta_one = datetime.timedelta(hours=int(fgran) )

        # calculate the cutoff for the first threshold using the number of candles
        oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone='Europe/London',
                         dailyAlignment=22)

        start=anchor_point - delta_from_start
        end=anchor_point.isoformat()

        oanda.run(start=start.isoformat(),
                  end=end,
                  roll=True)

        candle_list= oanda.fetch_candleset()

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
            return (False,'NO_BOUNCE')
        elif len(self.bounces) > 1:
            warnings.warn("Too many bounces")
            return (False,'TOO_MANY')
        else:
            return (True,'OK')

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
            return (False,'NO_BOUNCE')
        else:
            return (True,'OK')

    def get_first_bounce(self,part='closeAsk'):
        '''
        Function to identify the first (most recent) bounce

        Parameters
        ----------
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        A bounce representing the last bounce
        '''

        self.set_bounces(part=part, HR_pips=self.HR_pips, threshold=self.threshold, min_dist=1, min_dist_res=1,
                         start=self.__period1st_bounce_point)

        min_dist_res=1
        HR_pips = self.HR_pips

        while(self.__validate1stbounce()[0] is False) and (min_dist_res <= 10) and (HR_pips<=200):
            if self.__validate1stbounce()[1]=='TOO_MANY':
                min_dist_res += 1
                warnings.warn("More than 2 bounces identified. "
                              "Will try with 'min_dist_res'={0}".format(min_dist_res))
                self.set_bounces(part=part, HR_pips=self.HR_pips, threshold=self.threshold, min_dist=1, min_dist_res=min_dist_res,
                                 start=self.__period1st_bounce_point)
            elif self.__validate1stbounce()[1]=='NO_BOUNCE':
                HR_pips += 5
                warnings.warn("Less than 1 bounce identified. "
                              "Will try with 'HR_pips'={0}".format(HR_pips))
                threshold=self.threshold
                while(threshold >= 0.1) and (self.__validate1stbounce()[1]=='NO_BOUNCE'):
                    threshold-=0.1
                    self.set_bounces(part=part, HR_pips=HR_pips, threshold=threshold, min_dist=1,
                                     min_dist_res=min_dist_res,
                                     start=self.__period1st_bounce_point)

        if len(self.bounces)<1:
            raise Exception("No first bounce found")

        return self.bounces[-1]

    def get_second_bounce(self, first, part='closeAsk'):
        '''
        Function to identify the 2nd bounce

        Parameters
        ----------
        first: tuple
               First bounce
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        A bounce representing the second bounce
        '''

        end=self.__get_time4candles(n=5, anchor_point=first[0])
        self.set_bounces(part=part, HR_pips=self.HR_pips, threshold=self.threshold, min_dist=1,
                         min_dist_res=10,
                         start=self.trend_i,end=end)

        HR_pips = self.HR_pips
        while (self.__validate2ndbounce()[1] == 'NO_BOUNCE') and (HR_pips<=200):
            HR_pips += 5
            warnings.warn("Less than 1 bounce identified. "
                          "Will try with 'HR_pips'={0}".format(HR_pips))
            threshold = self.threshold
            while (threshold >= 0.1) and (self.__validate2ndbounce()[1] == 'NO_BOUNCE'):
                threshold -= 0.1
                self.set_bounces(part=part, HR_pips=HR_pips, threshold=threshold, min_dist=1,
                                 min_dist_res=1,
                                 start=self.trend_i,end=end)

        if len(self.bounces) < 1:
            raise Exception("No second bounce found")

        return self.bounces[-1]

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

        first_bounce=self.get_first_bounce()
        second_bounce=self.get_second_bounce(first=first_bounce)

        final_bounces = [second_bounce, first_bounce]

        # check bounces from the second bounce with a stricter parameter set
        self.set_bounces(part=part, HR_pips=60, threshold=0.5, min_dist=5, min_dist_res=5,
                         end=second_bounce[0])

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
        self.set_diff_rsi()
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
        It will set the 'diff' attribute of the class and calculate
        the number of pips from the difference. The sign will be ignored
        and the absolute number of pips is returned
        '''

        diff = self.bounce_1st[1] - self.bounce_2nd[1]

        (first, second) = self.pair.split("_")
        if first == 'JPY' or second == 'JPY':
            diff=diff*100
        else:
            diff=diff*10000

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

        self.diff_rsi=rsi1st_val-rsi2nd_val

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

        candle_list = oanda.fetch_candleset(vol_cutoff=0)

        self.valley=len(candle_list)

