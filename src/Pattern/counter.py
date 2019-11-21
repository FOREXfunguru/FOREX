import pdb
import datetime
import config
import numpy as np
import matplotlib

matplotlib.use('PS')
import matplotlib.pyplot as plt

from oanda_api import OandaAPI
from candlelist import CandleList
from utils import *
from harea import HArea

class Counter(object):
    '''
    This class represents a trade showing Counter pattern

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
    bounces_lasttime: list, Optional
                      With Candles representing the bounces
    slope: float, Optional
           Float with the slope of trend conducting to entry
    HR_pips: int, Optional
             Number of pips over/below S/R used for trying to identify bounces
             Default: 200
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

    def __init__(self, pair, period= 3000, HR_pips=200, **kwargs):

        allowed_keys = [ 'id','start','timeframe','period','entry','trend_i', 'type', 'SL',
                        'TP','SR','RR','bounces','clist_period','clist_trend','lasttime',
                        'bounces_lasttime','slope','n_rsibounces','rsibounces_lengths',
                        'divergence','entry_onrsi','length_candles','length_pips']

        # get values from config file
        if 'period' in config.CT: period = config.CT['period']
        if 'HR_pips' in config.CT: HR_pips = config.CT['HR_pips']

        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        self.pair=pair
        self.period=period
        self.HR_pips = HR_pips
        self.start = datetime.datetime.strptime(self.start, '%Y-%m-%d %H:%M:%S')

        # init the CandleList from self.period to self.start
        self.__initclist()
        # calc_rsi
        self.clist_period.calc_rsi()

        if not hasattr(self, 'TP'):
            if not hasattr(self, 'RR'): raise Exception("Neither the RR not the TP is defined. Please provide RR")
            diff=(self.entry-self.SL)*self.RR
            self.TP=round(self.entry+diff,4)

        # instantiate an HArea object representing the self.SR in order to calculate the lasttime
        # price has been above/below SR
        resist = HArea(price=self.SR, pips=100, instrument=self.pair, granularity=self.timeframe)
        self.lasttime=self.clist_period.get_lasttime(resist)

        # set bounces_lasttime Class attribute
        self.bounces_fromlasttime()


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

        cl = CandleList(candle_list, self.pair, granularity=self.timeframe, id=self.id, type=self.type)

        self.clist_period=cl

    def __inarea_bounces(self, bounces, HRpips, part='closeAsk'):
        '''
        Function to identify the candles for which price is in the area defined
        by self.SR+HRpips and self.SR-HRpips

        Parameters
        ----------
        bounces: list
                 Containing the initial list of candles
        HR_pips: int, Optional
                 Number of pips over/below S/R used for trying to identify bounces
                 Default: 200
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
            # print("u:{0}-l:{1}|p:{2}|t:{3}".format(upper, lower, price,c.time))
            if price >= lower and price <= upper:
                in_area_list.append(c)

        return in_area_list

    def set_bounces(self, part='closeAsk'):
        '''
        Function to get the bounces. For this, Zigzag will be used

        Parameters
        ----------
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        It will set the bounces attribute
        '''

        pivotlist = self.clist_period.get_pivotlist(th_up=config.CT['threshold_bounces'],
                                                    th_down=-config.CT['threshold_bounces'])

        bounces = pivotlist.plist

        arr = np.array(self.clist_period.clist)

        # consider type of trade in order to select peaks or valleys
        if self.type == 'short':
            bounce_candles = arr[bounces == 1]
        elif self.type == 'long':
            bounce_candles = arr[bounces == -1]

        in_area_list = []

        in_area_list = self.__inarea_bounces(bounce_candles, part=part, HRpips=self.HR_pips)

        outfile = "{0}/{1}.final_bounces.png".format(config.PNGFILES['bounces'],
                                                     self.id.replace(' ', '_'))
        outfile_rsi = "{0}/{1}.final_rsi.png".format(config.PNGFILES['rsi'],
                                                     self.id.replace(' ', '_'))
        pdb.set_trace()

        self.bounces= in_area_list

        self.plot_bounces(outfile_prices=outfile, outfile_rsi=outfile_rsi, part= config.CT['part'])


    def plot_bounces(self, outfile_prices, outfile_rsi, part='closeAsk'):
        '''
        Function to plot all bounces, the start of the trend and rsi values for this trade

        Parameters
        ----------
        outfile_prices : filename
                         for output file for prices plot
        outfile_rsi : filename
                      for output file for rsi plot
        part: str
              Candle part used for the calculation. Default='closeAsk'
        '''

        prices = []
        rsi = []
        datetimes = []
        for c in self.clist_period.clist:
            prices.append(getattr(c, part))
            rsi.append(getattr(c,'rsi'))
            datetimes.append(c.time)

        pdb.set_trace()
        # plotting the rsi values
        fig_rsi = plt.figure(figsize=config.PNGFILES['fig_sizes'])
        ax_rsi = plt.axes()
        ax_rsi.plot(datetimes, rsi, color="black")
        fig_rsi.savefig(outfile_rsi, format='png')

        # plotting the prices for part
        fig = plt.figure(figsize=config.PNGFILES['fig_sizes'])
        ax = plt.axes()
        ax.plot(datetimes, prices, color="black")

        final_bounces=self.bounces
        for b in final_bounces:
            dt = b.time
            ix = datetimes.index(dt)
            plt.scatter(datetimes[ix], prices[ix], s=50)

        fig.savefig(outfile_prices, format='png')

    def bounces_fromlasttime(self):
        '''
        Function to get the bounces occurring after last_time

        Returns
        -------
        Will set the bounces_lasttime class attribute
        '''

        bounces = [n for n in self.bounces if n.time >= self.lasttime]

        self.bounces_lasttime = bounces

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
