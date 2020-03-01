import pdb
import matplotlib

matplotlib.use('PS')
import matplotlib.pyplot as plt

from ast import literal_eval
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
    trend_i : datetime, Required
              start of the trend
    pivots : PivotList, Optional
              PivotList object with Pivots in the self.trade.SR
    clist_period : CandleList, Optional
                   Candlelist extending back (defined by 'period') in time since the start of the pattern

    pivots_lasttime : Pivotlist, Optional
                      PivotList with Pivots occurring after 'lasttime'
    init_feats : Bool, Optional
                 If true, then it will initialize several Counter feats
    n_rsibounces : int, Optional
                   Number of rsi bounces for trend conducting to start
    rsibounces_lengths : list, Optional
                         List with lengths for each rsi bounce
    entry_onrsi : bool, Optional
                  Is entry candle on rsi territory
    lasttime : datetime, Optional
               Last time price has been above/below self.trade.SR
    length_candles : int, Optional
                     Number of candles in self.clist_trend
    length_pips : int, Optional
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

    def __init__(self, trade, settingf=None, settings=None, init_feats=False, **kwargs):

        self.settingf = settingf
        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

        allowed_keys = ['id', 'trend_i', 'pivots', 'clist_period','lasttime',
                        'pivots_lasttime', 'n_rsibounces', 'rsibounces_lengths',
                        'entry_onrsi', 'length_candles', 'length_pips', 'SMA',
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

        if init_feats is True:
            self.set_lasttime()
            self.set_pivots()
            self.set_pivots_lasttime()
            self.set_score_lasttime()

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

        cl = CandleList(candle_list,
                        settingf=self.settingf,
                        instrument=self.trade.pair,
                        granularity=self.trade.timeframe,
                        id=self.id,
                        type=self.trade.type)

        self.clist_period = cl

    def set_lasttime(self):
        '''
        Function to set the lasttime class attribute

        returns
        -------
        Nothing
        '''
        # instantiate an HArea object representing the self.SR in order to calculate the lasttime
        # price has been above/below SR
        resist = HArea(price=self.trade.SR,
                       pips=self.settings.getint('trade', 'hr_pips'),
                       instrument=self.trade.pair,
                       granularity=self.trade.timeframe,
                       settings=self.settings)

        self.lasttime = self.clist_period.get_lasttime(resist)

    def __inarea_pivots(self,
                        pivots,
                        last_pivot=True):
        '''
        Function to identify the candles for which price is in the area defined
        by self.SR+HRpips and self.SR-HRpips

        Parameters
        ----------
        pivots: PivotList
        runmerge_pre: Boolean
                      Run PivotList's 'merge_pre' function. Default: False
        runmerge_aft: Boolean
                      Run PivotList's 'merge_aft' function. Default: False
        last_pivot: Boolean
                    If true, then the last pivot will be considered as it is part
                    of the setup. Default: False

        Returns
        -------
        PivotList with pivots that are in the area
        '''
        # get bounces in the horizontal SR area
        lower = substract_pips2price(self.trade.pair,
                                     self.trade.SR,
                                     self.settings.getint('pivots',
                                                          'hr_pips'))
        upper = add_pips2price(self.trade.pair,
                               self.trade.SR,
                               self.settings.getint('pivots',
                                                    'hr_pips'))
        pl = []
        for p in pivots.plist:
            # always consider the last pivot in bounces.plist as in_area as this part of the entry setup
            if pivots.plist[-1].candle.time == p.candle.time and last_pivot is True:
                if self.settings.getboolean('counter', 'runmerge_pre') is True and p.pre is not None:
                    p.merge_pre(slist=pivots.slist)
                if self.settings.getboolean('counter', 'runmerge_aft') is True and p.aft is not None:
                    p.merge_aft(slist=pivots.slist)
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
                        if self.settings.get('counter', 'runmerge_pre') is True and p.pre is not None:
                            p.merge_pre(slist=pivots.slist)
                        if self.settings.get('counter', 'runmerge_aft') is True and p.aft is not None:
                            p.merge_aft(slist=pivots.slist)
                        #check if this Pivot already exist in pl
                        p_seen=False
                        for op in pl:
                            if op.candle.time == p.candle.time:
                                p_seen=True
                        if p_seen is False:
                            pl.append(p)

        return PivotList(plist=pl,
                         clist=pivots.clist,
                         slist=pivots.slist)

    def set_pivots(self):
        '''
        Function to get the pivots as calculated by the Zigzag module

        Parameters
        ----------
        outfile : file
                  .png file for output. Required

        Returns
        -------
        It will set the pivots attribute, which is a PivotList object with Pivots
        in the area
        '''

        # get PivotList using self.clist_period
        pivotlist = self.clist_period.get_pivotlist()
        # get PivotList in area
        in_area_list = self.__inarea_pivots(pivotlist)

        #calculate score for Pivots
        pl = []
        for p in in_area_list.plist:
            p.calc_score()
            pl.append(p)

        self.pivots = PivotList(plist=pl,
                                clist=in_area_list.clist,
                                slist=in_area_list.slist)

        if self.settings.getboolean('pivots', 'plot') is True:
            outfile = self.settings.\
                          get('images', 'outdir')+"/pivots/{0}.sel_pivots.png".format(self.id.replace(' ', '_'))
            outfile_rsi = self.settings.\
                              get('images', 'outdir')+"/pivots/{0}.final_rsi.png".format(self.id.replace(' ', '_'))

            self.plot_pivots(outfile_prices=outfile,
                             outfile_rsi=outfile_rsi)

    def set_total_score(self):
        '''
        Function to calculate the total score after adding the score
        for each individual pivot
        It will set the 'total_score' class attribute

        returns
        -------
        Nothing
        '''

        tot_score = 0
        for p in self.pivots.plist:
            tot_score += p.score

        self.total_score = tot_score

    def plot_pivots(self, outfile_prices, outfile_rsi):
        '''
        Function to plot all pivots that are in the area

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
            prices.append(getattr(c, self.settings.get('general', 'part')))
            rsi.append(getattr(c, 'rsi'))
            datetimes.append(c.time)

        # getting the fig size from settings
        figsize = literal_eval(self.settings.get('images', 'size'))

        # plotting the rsi values
        fig_rsi = plt.figure(figsize=figsize)
        ax_rsi = plt.axes()
        ax_rsi.plot(datetimes, rsi, color="black")
        fig_rsi.savefig(outfile_rsi, format='png')

        # plotting the prices for part
        fig = plt.figure(figsize=figsize)
        ax = plt.axes()
        ax.plot(datetimes, prices, color="black")

        final_pivots = self.pivots
        for p in final_pivots.plist:
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

    def set_pivots_lasttime(self):
        '''
        Function to get the pivots occurring after last_time and setting
        the class 'pivots_lasttime'

        Returns
        -------
        Nothing
        '''

        pl = []
        for p in self.pivots.plist:
            if p.candle.time >= self.lasttime:
                pl.append(p)

        self.pivots_lasttime = PivotList(plist=pl,
                                         clist=self.pivots.clist,
                                         slist=self.pivots.slist)

    def set_score_lasttime(self):
        '''
        Function to calculate the pivot score for all bounces from lasttime
        It will set the 'score_lasttime' class attribute
        '''

        tot_score = 0
        for p in self.pivots_lasttime.plist:
            tot_score += p.score

        self.score_lasttime = tot_score

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key,
                                               value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
