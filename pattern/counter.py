import matplotlib
import pdb
import logging

matplotlib.use('PS')
import matplotlib.pyplot as plt

from ast import literal_eval
from apis.oanda_api import OandaAPI
from candle.candlelist import CandleList
from harea.harea import HArea
from pivot.pivotlist import *
from configparser import ConfigParser
from utils import periodToDelta, substract_pips2price, add_pips2price

logging.basicConfig(level=logging.INFO)

# create logger
c_logger = logging.getLogger(__name__)

class Counter(object):
    '''
    This class represents a trade showing Counter pattern

    Class variables
    ---------------

    trend_i : datetime, Required
              start of the trend
    pips_c_trend : float, Optional
                   This value represents the average number of pips for each candle from
                   self.trend_i up to self.start
    pivots : PivotList, Optional
              PivotList object with Pivots in the self.trade.SR
    clist_period : CandleList, Optional
                   Candlelist extending back (defined by 'period') in time since the start of the pattern
    pivots_lasttime : Pivotlist, Optional
                      PivotList with Pivots occurring after 'lasttime'
    score_pivot : int, Optional
                  Score per pivot.
                  This will be the result of dividing the
                  self.total_score/self.pivots
    score_pivot_lasttime : int, Optional
                           Score per pivot for all pivots_lasttime
                           This will be the result of dividing the
                           self.score_lasttime/self.pivots_lasttime
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
    max_min_rsi : float, Optional
                  max or min RSI for CandleList slice
                  going from self.start-settings.getint('counter', rsi_period') to self.start.
    settingf : str, Optional
               Path to *.ini file with settings
    settings : ConfigParser object generated using 'settingf'
               Optional
    '''

    def __init__(self, trade, settingf=None, settings=None, init_feats=False, **kwargs):

        c_logger.debug("Initializing counter object")

        self.settingf = settingf
        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

        allowed_keys = ['trend_i', 'pivots', 'clist_period','lasttime',
                        'pivots_lasttime', 'n_rsibounces', 'rsibounces_lengths',
                        'entry_onrsi', 'length_candles', 'length_pips', 'SMA',
                        'total_score', 'score_lasttime']

        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        self.trade = trade

        # init the CandleList from self.trade.start-self.settings.getint('counter', 'period')
        # to self.trade.start this will set the self.clist_period class attribute
        self.__initclist()
        # calc_rsi
        if self.clist_period is None:
            c_logger.warn("No 'self.clist_period' defined. Skipping 'calc_rsi' and 'init_feats' methods")
            init_feats = False
        else:
            self.clist_period.calc_rsi()
        if not hasattr(self.trade, 'TP'):
            if not hasattr(self, 'RR'):
                raise Exception("Neither the RR not the TP "
                                "is defined. Please provide RR")

            diff = (self.trade.entry-self.trade.SL)*self.trade.RR
            self.trade.TP = round(self.trade.entry+diff, 4)

        if init_feats is True:
            self.entry_onrsi = self.is_entry_onrsi()
            self.set_lasttime()
            self.set_pivots()
            self.set_total_score()
            self.set_pivots_lasttime()
            self.set_score_lasttime()
            self.set_score_pivot()
            self.set_score_pivot_lasttime()
            self.set_trend_i()
            self.pips_c_trend = self.calc_pips_c_trend()
            self.set_max_min_rsi()

        c_logger.debug("Done initializing counter object")

    def __initclist(self):
        '''
        Private function to initialize the CandleList object that goes from self.trade.start
        to self.period

        This will set the self.clist_period class attribute

        Returns
        -------
        None if Oanda API query was not successful
        '''

        delta_period = periodToDelta(self.settings.getint('counter', 'period'),
                                     self.trade.timeframe)
        delta_1 = periodToDelta(1, self.trade.timeframe)
        start = self.trade.start - delta_period  # get the start datetime for this CandleList period
        end = self.trade.start + delta_1  # increase self.start by one candle to include self.start

        oanda = OandaAPI(url=self.settings.get('oanda_api', 'url'),
                         instrument=self.trade.pair,
                         granularity=self.trade.timeframe,
                         settingf=self.settingf,
                         settings=self.settings)

        resp = oanda.run(start=start.isoformat(),
                         end=end.isoformat())

        if resp == 200:

            candle_list = oanda.fetch_candleset()

            cl = CandleList(candle_list,
                            settingf=self.settingf,
                            settings=self.settings,
                            instrument=self.trade.pair,
                            granularity=self.trade.timeframe,
                            id=self.trade.id,
                            type=self.trade.type)

            self.clist_period = cl
        else:
            c_logger.warn("API query was not OK. 'self.clist_period' will be None ")
            self.clist_period = None

    def set_max_min_rsi(self):
        """
        Function to calculate the max or min RSI for CandleList slice
        going from self.start-settings.getint('counter', rsi_period') to self.start.
        It will also set the max_min_rsi self attribute

        Returns
        -------
        float : The max (if short trade) or min (long trade) rsi value
                in the candlelist
        """
        c_logger.debug("Running set_max_min_rsi")

        ix = self.settings.getint('counter', 'rsi_period')
        sub_clist = self.clist_period.clist[-ix:]
        rsi_list = [x.rsi for x in sub_clist]
        first = None
        for x in reversed(rsi_list):
            if first is None:
                first = x
            elif self.trade.type == 'short':
                if x > first:
                    first = x
            elif self.trade.type == 'long':
                if x < first:
                    first = x

        self.max_min_rsi = round(first, 2)

        c_logger.debug("Done set_max_min_rsi")

        return round(first, 2)

    def is_entry_onrsi(self):
        '''
        Function to check if self.trade.start is on RSI

        Returns
        -------
        True if self.trade.start is on RSI (i.e. RSI>=70 or RSI<=30)
        False otherwise
        '''
        if self.clist_period.clist[-1].rsi >= 70 or self.clist_period.clist[-1].rsi <= 30:
            return True
        else:
            return False

    def set_lasttime(self):
        '''
        Function to set the lasttime class attribute

        returns
        -------
        Nothing
        '''
        c_logger.debug("Running set_lasttime")

        # instantiate an HArea object representing the self.SR in order to calculate the lasttime
        # price has been above/below SR
        resist = HArea(price=self.trade.SR,
                       pips=self.settings.getint('harea', 'hr_pips'),
                       instrument=self.trade.pair,
                       granularity=self.trade.timeframe,
                       settings=self.settings)

        self.lasttime = self.clist_period.get_lasttime(resist)

        c_logger.debug("Done set_lasttime")


    def __inarea_pivots(self,
                        pivots,
                        last_pivot=True):
        '''
        Function to identify the candles for which price is in the area defined
        by self.SR+HRpips and self.SR-HRpips

        Parameters
        ----------
        pivots: PivotList with pivots
        last_pivot: Boolean
                    If True, then the last pivot will be considered as it is part
                    of the setup. Default: True

        Returns
        -------
        PivotList with pivots that are in the area
        '''

        c_logger.debug("Running __inarea_pivots")

        # get bounces in the horizontal SR area
        lower = substract_pips2price(self.trade.pair,
                                     self.trade.SR,
                                     self.settings.getint('pivots',
                                                          'hr_pips'))
        upper = add_pips2price(self.trade.pair,
                               self.trade.SR,
                               self.settings.getint('pivots',
                                                    'hr_pips'))

        c_logger.debug("SR U-limit: {0}; L-limit: {1}".format(round(upper, 4), round(lower, 4)))

        pl = []
        for p in pivots.plist:
            # always consider the last pivot in bounces.plist as in_area as this part of the entry setup
            if pivots.plist[-1].candle.time == p.candle.time and last_pivot is True:
                adj_t = p.adjust_pivottime(clistO=pivots.clist)
                # get new CandleList with new adjusted time for the end
                newclist = pivots.clist.slice(start=pivots.clist.clist[0].time,
                                              end=adj_t)
                newp = newclist.get_pivotlist(self.settings.getfloat('pivots', 'th_bounces')).plist[-1]
                if self.settings.getboolean('counter', 'runmerge_pre') is True and newp.pre is not None:
                    newp.merge_pre(slist=pivots.slist,
                                   n_candles=self.settings.getint('pivots', 'n_candles'),
                                   diff_th=self.settings.getint('pivots', 'diff_th'))
                if self.settings.getboolean('counter', 'runmerge_aft') is True and newp.aft is not None:
                    newp.merge_aft(slist=pivots.slist,
                                   n_candles=self.settings.getint('pivots', 'n_candles'),
                                   diff_th=self.settings.getint('pivots', 'diff_th'))
                pl.append(newp)
            else:
                part_list = ['close{0}'.format(self.settings.get('general', 'bit'))]
                if p.type == 1:
                    part_list.append('high{0}'.format(self.settings.get('general', 'bit')))
                elif p.type == -1:
                    part_list.append('low{0}'.format(self.settings.get('general', 'bit')))

                # initialize candle features to be sure that midAsk or midBid are
                # initialized
                p.candle.set_candle_features()
                for part in part_list:
                    price = getattr(p.candle, part)
                    # only consider pivots in the area
                    if price >= lower and price <= upper:
                        # check if this pivot already exists in pl
                        p_seen = False
                        for op in pl:
                            if op.candle.time == p.candle.time:
                                p_seen = True

                        if p_seen is False:
                            c_logger.debug("Pivot {0} identified in area".format(p.candle.time))
                            if self.settings.getboolean('counter', 'runmerge_pre') is True and p.pre is not None:
                                p.merge_pre(slist=pivots.slist,
                                            n_candles=self.settings.getint('pivots', 'n_candles'),
                                            diff_th=self.settings.getint('pivots', 'diff_th'))
                            if self.settings.getboolean('counter', 'runmerge_aft') is True and p.aft is not None:
                                p.merge_aft(slist=pivots.slist,
                                            n_candles=self.settings.getint('pivots', 'n_candles'),
                                            diff_th=self.settings.getint('pivots', 'diff_th'))
                            pl.append(p)

        c_logger.debug("Done __inarea_pivots")

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
        c_logger.debug("Running set_pivots")

        # get PivotList using self.clist_period
        pivotlist = self.clist_period.get_pivotlist(self.settings.getfloat('pivots', 'th_bounces'))
        # get PivotList in area
        in_area_list = self.__inarea_pivots(pivotlist, last_pivot = self.settings.getboolean('pivots', 'last_pivot'))

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
                          get('images', 'outdir')+"/pivots/{0}.sel_pivots.png".format(self.trade.id.replace(' ', '_'))
            outfile_rsi = self.settings.\
                              get('images', 'outdir')+"/pivots/{0}.final_rsi.png".format(self.trade.id.replace(' ', '_'))

            self.plot_pivots(outfile_prices=outfile,
                             outfile_rsi=outfile_rsi)

        c_logger.debug("Done set_pivots")

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

    def set_trend_i(self):
        '''
        Function to set the trend_i attribute

        returns
        -------
        Nothing
        '''

        merged_s = self.clist_period.calc_itrend()

        if self.trade.type == "long":
            candle = merged_s.get_highest()
        elif self.trade.type == "short":
            candle = merged_s.get_lowest()

        self.trend_i = candle.time

    def calc_pips_c_trend(self):
        '''
        Function to calculate the pips_c_trend

        Returns
        -------
        Float with number of pips for the trend_i
        '''

        oanda = OandaAPI(url=self.settings.get('oanda_api', 'url'),
                         instrument=self.trade.pair,
                         granularity=self.trade.timeframe,
                         settingf=self.settingf,
                         settings=self.settings)

        resp = oanda.run(start=self.trend_i.isoformat(),
                         end=self.trade.start.isoformat())

        if resp == 200:

            candle_list = oanda.fetch_candleset()

            cl = CandleList(candle_list,
                            settingf=self.settingf,
                            settings=self.settings,
                            instrument=self.trade.pair,
                            granularity=self.trade.timeframe,
                            id=self.trade.id,
                            type=self.trade.type)

            pips_c_trend = cl.get_length_pips()/cl.get_length_candles()

            return round(pips_c_trend, 1)
        else:
            c_logger.warn("API query was not OK. 'pips_c_trend' could not be calculated")



    def set_score_pivot(self):
        '''
        Function to calculate the score per pivot.
        This will be the result of dividing the
        self.total_score/self.pivots
        It will set the 'score_pivot' class attribute

        returns
        -------
        Nothing
        '''
        if not hasattr(self, 'pivots'):
            raise Exception("'pivots' is not defined")
        if not hasattr(self, 'total_score'):
            raise Exception("'total_score' is not defined")

        if len(self.pivots.plist) == 0:
            self.score_pivot = 0
        else:
            self.score_pivot = self.total_score/len(self.pivots.plist)

    def set_score_pivot_lasttime(self):
        '''
        Function to calculate the score per pivot for all pivots_lasttime
        This will be the result of dividing the
        self.score_lasttime/self.pivots_lasttime
        It will set the 'score_pivot_lasttime' class attribute

        returns
        -------
        Nothing
        '''

        if not hasattr(self, 'pivots_lasttime'):
            raise Exception("'pivots_lasttime' is not defined")
        if not hasattr(self, 'score_lasttime'):
            raise Exception("'score_lasttime' is not defined")

        if len(self.pivots_lasttime.plist) == 0:
            self.score_pivot_lasttime = 0
        else:
            self.score_pivot_lasttime = self.score_lasttime / len(self.pivots_lasttime.plist)

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
        c_logger.debug("Running plot_pivots")

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

        c_logger.debug("plot_pivots Done")

    def set_pivots_lasttime(self):
        '''
        Function to get the pivots occurring after last_time and setting
        the class 'pivots_lasttime'

        Returns
        -------
        Nothing
        '''

        c_logger.debug("Running set_pivots_lasttime")

        pl = []
        for p in self.pivots.plist:
            if p.candle.time >= self.lasttime:
                pl.append(p)

        self.pivots_lasttime = PivotList(plist=pl,
                                         clist=self.pivots.clist,
                                         slist=self.pivots.slist)
        c_logger.debug("Done set_pivots_lasttime")

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
