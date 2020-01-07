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
from pivotlist import *

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
             List with Candle objects for price bounces at self.SR
    png_prefix: str, Required
                Output prefix
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
    SMA : str, Optional
          Is there SMA support for this trade. Values: 'Y'/'N'
    '''

    def __init__(self, pair, png_prefix, period= 3000, HR_pips=200, **kwargs):

        allowed_keys = [ 'id','start','timeframe','period','entry','trend_i', 'type', 'SL',
                        'TP','SR','RR','bounces','clist_period','clist_trend','lasttime',
                        'bounces_lasttime','slope','n_rsibounces','rsibounces_lengths',
                        'divergence','entry_onrsi','length_candles','length_pips', 'SMA']

        # get values from config file
        if 'period' in config.CT: period = config.CT['period']
        if 'HR_pips' in config.CT: HR_pips = config.CT['HR_pips']

        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        self.pair=pair
        self.png_prefix=png_prefix
        self.period=period
        self.HR_pips = HR_pips
        self.start = datetime.datetime.strptime(self.start,
                                                '%Y-%m-%d %H:%M:%S')

        # init the CandleList from self.period to self.start
        # this will set the self.clist_period class attribute
        self.__initclist()
        # calc_rsi
        self.clist_period.calc_rsi()

        if not hasattr(self, 'TP'):
            if not hasattr(self, 'RR'): raise Exception("Neither the RR not the TP is defined. Please provide RR")
            diff=(self.entry-self.SL)*self.RR
            self.TP=round(self.entry+diff,4)

        # instantiate an HArea object representing the self.SR in order to calculate the lasttime
        # price has been above/below SR
        resist = HArea(price=self.SR, pips=100, instrument=self.pair,
                       granularity=self.timeframe)
        self.lasttime=self.clist_period.get_lasttime(resist)

        #initialize 'bounces' Class attribute
        self.set_bounces(doPlot=True, outfile=png_prefix+".bounces.png",
                         part='closeAsk')

        # set bounces_lasttime Class attribute
       # self.bounces_fromlasttime()


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

        cl = CandleList(candle_list, self.pair, granularity=self.timeframe,
                        id=self.id, type=self.type)

        self.clist_period=cl

    def __inarea_bounces(self, bounces, HRpips, part='midAsk'):
        '''
        Function to identify the candles for which price is in the area defined
        by self.SR+HRpips and self.SR-HRpips

        Parameters
        ----------
        bounces: PivotList
        HR_pips: int, Optional
                 Number of pips over/below S/R used for trying to identify bounces
                 Required.
        part: str
              Candle part used for the calculation. Default='midAsk'

        Returns
        -------
        list with bounces that are in the area
        '''
        # get bounces in the horizontal SR area
        lower = substract_pips2price(self.pair, self.SR, HRpips)
        upper = add_pips2price(self.pair, self.SR, HRpips)

        pl=[]
        for p in bounces.plist:
            # initialize candle features to be sure that midAsk or midBid are
            # initialized
            p.candle.set_candle_features()
            price = getattr(p.candle, part)
            print("Price: {0}; Upper: {1}; Lower: {2}; time: {3}".format(price, upper, lower, p.candle.time))
            if price >= lower and price <= upper:
                print("inarea\n")
                pl.append(p)

        return PivotList(plist=pl,clist=bounces.clist, slist=bounces.slist)

    def set_bounces(self, outfile, part='midAsk', doPlot=False):
        '''
        Function to get the bounces. For this, Zigzag will be used

        Parameters
        ----------
        outfile : file
                  .png file for output. Required
        part: str
              Candle part used for the calculation. Default='midAsk'
        doPlot: boolean
                If true, then generate a plot with bounces and a plot with rsi.
                Default: False

        Returns
        -------
        It will set the bounces attribute
        '''

        # get PivotList using self.clist_period
        pivotlist = self.clist_period.get_pivotlist(
                outfile=outfile,
                th_up=config.CT['threshold_bounces'],
                th_down=-config.CT['threshold_bounces'],
                part=config.CT['part'])

        # consider type of trade in order to select peaks or valleys
       # if self.type == 'short':
       #     bounces = pivotlist.fetch_by_type(type=-1)
       # elif self.type == 'long':
       #     bounces = pivotlist.fetch_by_type(type=1)

        # get bounces in area
        in_area_list = self.__inarea_bounces(pivotlist, part=part, HRpips=self.HR_pips)

        self.bounces= in_area_list

        if doPlot is True:
            outfile = self.png_prefix+".{0}.sel_pivots.png".format(self.id.replace(' ', '_'))
            outfile_rsi = self.png_prefix+".{0}.final_rsi.png".format(self.id.replace(' ', '_'))

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
        for p in final_bounces.plist:
            dt = p.candle.time
            ix = datetimes.index(dt)
            # prepare the plot for 'pre' segment
            if p.pre is not None:
                # merge pre segments
                p.merge_pre(slist=final_bounces.slist, n_candles=5)
                ix_pre_s = datetimes.index(p.pre.start())
                plt.scatter(datetimes[ix_pre_s], prices[ix_pre_s], s=100, marker='v')
                ix_pre_e = datetimes.index(p.pre.end())
                plt.scatter(datetimes[ix_pre_e], prices[ix_pre_e], s=100, marker='v')
            # prepare the plot for 'aft' segment
            if p.aft is not None:
                # merge aft segments
                p.merge_aft(slist=final_bounces.slist, n_candles=5)
                ix_aft_s = datetimes.index(p.aft.start())
                plt.scatter(datetimes[ix_aft_s], prices[ix_aft_s], s=100, marker='v')
                ix_aft_e = datetimes.index(p.aft.end())
                plt.scatter(datetimes[ix_aft_e], prices[ix_aft_e], s=100, marker='v')
            # plot
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
