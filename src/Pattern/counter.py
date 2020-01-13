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
    png_prefix: str, Optional
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
    total_score : int, Optional
                  Total (sum of each pivot score) pivot score for all bounces (bounces class attr)
    score_lasttime : int, Optional
                     Sum of each pivot score for all pivots after lasttime (bounces_lasttime class attr)

    '''

    def __init__(self, pair, period= 3000, HR_pips=200, **kwargs):

        allowed_keys = [ 'id','start','timeframe','period','entry','trend_i', 'type', 'SL',
                        'TP','SR','RR','bounces','clist_period','clist_trend','lasttime',
                        'bounces_lasttime','slope','n_rsibounces','rsibounces_lengths',
                        'divergence','entry_onrsi','length_candles','length_pips', 'SMA',
                        'total_score','score_lasttime','png_prefix']

        # get values from config file
        if 'period' in config.CT: period = config.CT['period']
        if 'HR_pips' in config.CT: HR_pips = config.CT['HR_pips']
        if 'png_prefix' in config.CT: png_prefix = config.CT['png_prefix']

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
        resist = HArea(price=self.SR, pips=config.CT['HR_pips'], instrument=self.pair,
                       granularity=self.timeframe)
        self.lasttime=self.clist_period.get_lasttime(resist)

        #initialize 'bounces' Class attribute
        self.set_bounces(doPlot=True, outfile=self.png_prefix+".{0}.all_pivots.png".format(self.id.replace(' ','_')),
                         part='closeAsk')

        # set total_score attr
        self.calc_score()

        # set bounces_lasttime Class attribute
        self.bounces_fromlasttime()
        self.calc_score_lasttime()


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

    def __inarea_bounces(self, bounces, HRpips, part_list=['midAsk'], runmerge_pre=False,
                         runmerge_aft=False):
        '''
        Function to identify the candles for which price is in the area defined
        by self.SR+HRpips and self.SR-HRpips

        Parameters
        ----------
        bounces: PivotList
        HR_pips: int, Optional
                 Number of pips over/below S/R used for trying to identify bounces
                 Required.
        part_list: List
              List with candle parts used for the calculation. Default=['midAsk'].
              Optional
        runmerge_pre: Boolean
                      Run PivotList's 'merge_pre' function. Default: False
        runmerge_aft: Boolean
                      Run PivotList's 'merge_aft' function. Default: False

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
            for part in part_list:
                price = getattr(p.candle, part)
                if price >= lower and price <= upper:
                    if runmerge_pre is True and p.pre is not None:
                        p.merge_pre(slist=bounces.slist, n_candles=20)
                    if runmerge_aft is True and p.aft is not None:
                        p.merge_aft(slist=bounces.slist, n_candles=20)
                    #check if this Pivot already exist in pl
                    p_seen=False
                    for op in pl:
                        if op.candle.time==p.candle.time:
                            p_seen=True
                    if p_seen is False:
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

        # get bounces in area for 2 different Candle parts
        part_list=[config.CT['part']]
        if self.type=='short':
            part_list.append('highAsk')
        elif self.type=='long':
            part_list.append('lowAsk')

        in_area_list = self.__inarea_bounces(pivotlist, part_list=part_list, HRpips=self.HR_pips,runmerge_pre=True,
                                             runmerge_aft=True)

        #calculate score for Pivots
        pl=[]
        for p in in_area_list.plist:
            p.calc_score()
            pl.append(p)

        self.bounces=PivotList(plist=pl, clist=in_area_list.clist, slist=in_area_list.slist)

        if doPlot is True:
            outfile = self.png_prefix+".{0}.sel_pivots.png".format(self.id.replace(' ', '_'))
            outfile_rsi = self.png_prefix+".{0}.final_rsi.png".format(self.id.replace(' ', '_'))

            self.plot_bounces(outfile_prices=outfile, outfile_rsi=outfile_rsi, part= config.CT['part'])

    def calc_score(self):
        '''
        Function to calculate the total (sum of each pivot score) pivot score for all bounces
        It will set the 'total_score' class attribute
        '''

        tot_score=0
        for p in self.bounces.plist:
            tot_score+=p.score

        self.total_score=tot_score



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
                ix_pre_s = datetimes.index(p.pre.start())
                plt.scatter(datetimes[ix_pre_s], prices[ix_pre_s], s=100, marker='v')
            # prepare the plot for 'aft' segment
            if p.aft is not None:
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
        Will set the bounces_lasttime class attribute with a PivotList
        of the pivots after lasttime
        '''

        pl = []
        for p in self.bounces.plist:
            if p.candle.time>=self.lasttime:
                pl.append(p)

        self.bounces_lasttime = PivotList(plist=pl, clist=self.bounces.clist, slist=self.bounces.slist)

    def calc_score_lasttime(self):
        '''
        Function to calculate the pivot score for all bounces from lasttime
        It will set the 'score_lasttime' class attribute
        '''

        tot_score = 0
        for p in self.bounces_lasttime.plist:
            tot_score += p.score

        self.score_lasttime = tot_score

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
