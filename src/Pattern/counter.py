import pdb
import matplotlib

matplotlib.use('PS')
import matplotlib.pyplot as plt

from oanda_api import OandaAPI
from candlelist import CandleList
from harea import HArea
from pivotlist import *
from configparser import ConfigParser


class Counter(object):
    '''
    This class represents a trade showing Counter pattern

    Class variables
    ---------------

    id : str, Required
         Id used for this object
    trend_i: datetime, Required
             start of the trend
    bounces: list, Optional
             List with Candle objects for price bounces at self.SR
    clist_period: CandleList, Optional
                  Candlelist extending back (defined by 'period') in time since the start of the pattern
    clist_trend: CandleList, Optional
                 CandleList extending back to datetime defined by self.trend_i
    bounces_lasttime: list, Optional
                      With Candles representing the bounces
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
    SMA : str, Optional
          Is there SMA support for this trade. Values: 'Y'/'N'
    total_score : int, Optional
                  Total (sum of each pivot score) pivot score for all bounces (bounces class attr)
    score_lasttime : int, Optional
                     Sum of each pivot score for all pivots after lasttime (bounces_lasttime class attr)
    settingf : str, Optional
               Path to *.ini file with settings
    '''

    def __init__(self, trade, settingf=None, settings=None, **kwargs):

        self.settingf = settingf
        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

        allowed_keys = [ 'id', 'trend_i', 'bounces', 'clist_period', 'clist_trend','lasttime',
                        'bounces_lasttime', 'slope', 'n_rsibounces', 'rsibounces_lengths',
                        'divergence', 'entry_onrsi', 'length_candles', 'length_pips', 'SMA',
                        'total_score', 'score_lasttime']

        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        self.trade = trade

        # init the CandleList from self.period to self.trade.start
        # this will set the self.clist_period class attribute
        self.__initclist()
        # calc_rsi
        self.clist_period.calc_rsi()

        if not hasattr(self.trade, 'TP'):
            if not hasattr(self, 'RR'):
                raise Exception("Neither the RR not the TP "
                                "is defined. Please provide RR")

            diff = (self.trade.entry-self.trade.SL)*self.trade.RR
            self.trade.TP = round(self.trade.entry+diff, 4)

        pdb.set_trace()

        # instantiate an HArea object representing the self.SR in order to calculate the lasttime
        # price has been above/below SR
        resist = HArea(price=self.trade.SR,
                       instrument=self.trade.pair,
                       granularity=self.trade.timeframe,
                       settings=self.settings)

        self.lasttime = self.clist_period.get_lasttime(resist)

        #initialize 'bounces' Class attribute
        self.set_bounces(doPlot=True,
                         outfile=self.settings('general',
                                               'outfile')+".{0}.all_pivots.png".
                         format(self.id.replace(' ', '_')),
                         part=self.settings('general', 'part'))

        # set total_score attr
        self.calc_score()

        # set bounces_lasttime Class attribute
        self.bounces_fromlasttime()
        self.calc_score_lasttime()

    def __initclist(self):
        '''
        Private function to initialize the CandleList object that goes from self.trade.start
        to self.period

        This will set the self.clist_period class attribute
        '''

        delta_period = periodToDelta(self.settings.getint('counter', 'period'),
                                     self.trade.timeframe)
        delta_1 = periodToDelta(1, self.trade.timeframe)
        start = self.trade.start - delta_period  # get the start datetime for this CandleList period
        end = self.trade.start + delta_1  # increase self.start by one candle to include self.start

        oanda = OandaAPI(url=self.settings.get('oanda_api', 'url'),
                         instrument=self.trade.pair,
                         granularity=self.trade.timeframe,
                         settingf=self.settingf)

        oanda.run(start=start.isoformat(),
                  end=end.isoformat())

        candle_list = oanda.fetch_candleset()
        pdb.set_trace()
        cl = CandleList(candle_list,
                        settingf=self.settingf,
                        instrument=self.trade.pair,
                        granularity=self.trade.timeframe,
                        id=self.id,
                        type=self.trade.type)

        self.clist_period = cl

    def __inarea_bounces(self,
                         bounces,
                         consider_last_bounce=True):
        '''
        Function to identify the candles for which price is in the area defined
        by self.SR+HRpips and self.SR-HRpips

        Parameters
        ----------
        bounces: PivotList
        runmerge_pre: Boolean
                      Run PivotList's 'merge_pre' function. Default: False
        runmerge_aft: Boolean
                      Run PivotList's 'merge_aft' function. Default: False
        consider_last_bounce: Boolean
                              If true, then the last bounce will be considered as it is part
                              of the setup. Default: False

        Returns
        -------
        list with bounces that are in the area
        '''
        # get bounces in the horizontal SR area
        lower = substract_pips2price(self.pair,
                                     self.SR,
                                     self.settings.getint('pivots','hr_pips'))
        upper = add_pips2price(self.pair,
                               self.SR,
                               self.settings.getint('pivots','hr_pips'))
        pl = []
        for p in bounces.plist:
            # always consider the last pivot in bounces.plist as in_area as this part of the entry setup
            if bounces.plist[-1].candle.time == p.candle.time and consider_last_bounce is True:
                if self.settings.getboolean('counter', 'run_merge_pre') is True and p.pre is not None:
                    p.merge_pre(slist=bounces.slist, n_candles=self.settings.getint('pivots', 'n_candles'))
                if self.settings.getboolean('counter', 'run_merge_aft') is True and p.aft is not None:
                    p.merge_aft(slist=bounces.slist, n_candles=self.settings.getint('pivots', 'n_candles'))
                pl.append(p)
            else:
                part_list=['close{0}'.format(self.settings.get('general', 'part'))]
                if p.type == 1:
                    part_list.append('high{0}'.format(self.settings.get('general', 'part')))
                elif p.type == -1:
                    part_list.append('low{0}'.format(self.settings.get('general', 'part')))

                # initialize candle features to be sure that midAsk or midBid are
                # initialized
                p.candle.set_candle_features()
                for part in part_list:
                    price = getattr(p.candle, self.settings.get('general', 'part'))
                    if price >= lower and price <= upper:
                        if self.settings.get('counter', 'run_'
                                                        'merge_pre') is True and p.pre is not None:
                            p.merge_pre(slist=bounces.slist,
                                        n_candles=self.settings.getint('pivots', 'n_candles'))
                        if self.settings.get('counter', 'runmerge_aft') is True and p.aft is not None:
                            p.merge_aft(slist=bounces.slist,
                                        n_candles=self.settings.getint('pivots', 'n_candles'))
                        #check if this Pivot already exist in pl
                        p_seen=False
                        for op in pl:
                            if op.candle.time == p.candle.time:
                                p_seen=True
                        if p_seen is False:
                            pl.append(p)

        return PivotList(plist=pl,
                         clist=bounces.clist,
                         slist=bounces.slist)

    def set_bounces(self, doPlot= False):
        '''
        Function to get the bounces. For this, Zigzag will be used

        Parameters
        ----------
        outfile : file
                  .png file for output. Required
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
                th_up=self.settings.getfloat('pivots', 'th_bounces'),
                th_down=-self.settings.getfloat('pivots', 'th_bounces'),
                part=self.settings.get('general','part'))

        in_area_list = self.__inarea_bounces(pivotlist,
                                             HRpips=self.HR_pips,
                                             runmerge_pre=True,
                                             runmerge_aft=True)

        #calculate score for Pivots
        pl=[]
        for p in in_area_list.plist:
            p.calc_score()
            pl.append(p)

        self.bounces = PivotList(plist=pl,
                                 clist=in_area_list.clist,
                                 slist=in_area_list.slist)

        if doPlot is True:
            outfile = self.png_prefix+".{0}.sel_pivots.png".format(self.id.replace(' ', '_'))
            outfile_rsi = self.png_prefix+".{0}.final_rsi.png".format(self.id.replace(' ', '_'))

            self.plot_bounces(outfile_prices=outfile,
                              outfile_rsi=outfile_rsi,
                              part= self.settings('general', 'part'))

    def calc_score(self):
        '''
        Function to calculate the total (sum of each pivot score) pivot score for all bounces
        It will set the 'total_score' class attribute
        '''

        tot_score = 0
        for p in self.bounces.plist:
            tot_score += p.score

        self.total_score = tot_score

    def plot_bounces(self, outfile_prices, outfile_rsi):
        '''
        Function to plot all bounces, the start of the trend and rsi values for this trade

        Parameters
        ----------
        outfile_prices : filename
                         for output file for prices plot
        outfile_rsi : filename
                      for output file for rsi plot
        '''

        prices = []
        rsi = []
        datetimes = []
        for c in self.clist_period.clist:
            prices.append(getattr(c, self.settings('general', 'part')))
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

        final_bounces = self.bounces
        for p in final_bounces.plist:
            dt = p.candle.time
            ix = datetimes.index(dt)
            # prepare the plot for 'pre' segment
            if p.pre is not None:
                ix_pre_s = datetimes.index(p.pre.start())
                plt.scatter(datetimes[ix_pre_s], prices[ix_pre_s], s=200, c='green', marker='v')
            # prepare the plot for 'aft' segment
            if p.aft is not None:
                ix_aft_e = datetimes.index(p.aft.end())
                plt.scatter(datetimes[ix_aft_e], prices[ix_aft_e], s=200, c='red', marker='v')
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
