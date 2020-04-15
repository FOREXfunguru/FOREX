from apis.oanda_api import OandaAPI
from configparser import ConfigParser
from trade_journal.trade import Trade
from trade_journal.trade_list import TradeList
from pattern.counter import Counter
from candle.candlelist import CandleList
from harea.harea import HArea
from harea.harealist import HAreaList

from utils import *
import pdb
import pandas as pd
import datetime
import re

class TradeBot(object):
    '''
    This class represents an automatic Trading bot

    Class variables
    ---------------
    start: datetime, Required
           Datetime that this Bot will start operating. i.e. 20-03-2017 08:20:00s
    end: datetime, Required
         Datetime that this Bot will end operating. i.e. 20-03-2020 08:20:00s
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    settingf : str, Optional
               Path to *.ini file with settings
    '''
    def __init__(self, start, end, pair, timeframe, settingf, settings=None):
        self.start = start
        self.end = end
        self.pair = pair
        self.timeframe = timeframe
        self.settingf = settingf
        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

    def __get_trade_type(self, ic, harea_sel, delta):
        '''
        Function to guess what is the trade type (short or long)
        for this possible trade

        Parameters
        ----------
        ic : Candle object
             Indecision candle for this trade
        harea_sel : HArea of this trade
        delta : Timedelta object corresponding to
                the time that needs to be increased

        Returns
        -------
        str: Trade type (long or short)
        '''

        oanda = OandaAPI(instrument=self.pair,
                         granularity=self.timeframe,
                         settingf=self.settingf)

        # n x delta controls how many candles to go back in time
        # to check
        start = ic.time - 6*delta
        end = ic.time

        oanda.run(start=start.isoformat(),
                  end=end.isoformat())

        short_ct = 0
        long_ct = 0
        candle_list = oanda.fetch_candleset()
        for c in candle_list:
            price = getattr(c, self.settings.get('general', 'part'))
            if price < harea_sel.price:
                short_ct += 1
            elif price > harea_sel.price:
                long_ct += 1
            elif price == harea_sel.price:
                continue

        if short_ct > long_ct:
            return 'short'
        elif short_ct < long_ct:
            return 'long'
        elif short_ct == long_ct:
            raise Exception("Trade type undefined")

    def prepare_trade(self, type, ic, harea_sel, delta):
        '''
        Prepare a Trade object
        and check if it is taken

        Parameters
        ----------
        type : str,
               Type of trade. 'short' or 'long'
        ic : Candle object
             Indecision candle for this trade
        harea_sel : HArea of this trade
        delta : Timedelta object corresponding to
                the time that needs to be increased

        Returns
        -------
        Trade object
        '''

        startO = ic.time + delta
        if type == 'short':
            # entry price will be the low of IC
            # SL price wil the be the high of IC
            entry_p = getattr(ic, "low{0}".format(self.settings.get('general', 'bit')))
            SL_p = getattr(ic, "high{0}".format(self.settings.get('general', 'bit')))
        elif type == 'long':
            # entry price will be the high of IC
            # SL price wil the be the low of IC
            entry_p = getattr(ic, "high{0}".format(self.settings.get('general', 'bit')))
            SL_p = getattr(ic, "low{0}".format(self.settings.get('general', 'bit')))

        startO = ic.time+delta
        t = Trade(
            id='{0}.bot'.format(self.pair),
            start=startO.strftime('%Y-%m-%d %H:%M:%S'),
            pair=self.pair,
            timeframe=self.timeframe,
            type=type,
            entry=entry_p,
            SR=harea_sel.price,
            SL=SL_p,
            RR=self.settings.getfloat('trade_bot', 'RR'),
            strat='counter',
            settingf=self.settingf)

        return t


    def run(self):
        '''
        This function will run the Bot from start to end
        one candle at a time

        Returns
        -------
        TradeList object with Trades taken. None if no trades
        were taken
        '''
        oanda = OandaAPI(instrument=self.pair,
                         granularity=self.timeframe,
                         settingf=self.settingf)
        delta = None
        nhours = None
        if self.timeframe == "D":
            nhours = 24
            delta = datetime.timedelta(hours=24)
        else:
            p1 = re.compile('^H')
            m1 = p1.match(self.timeframe)
            if m1:
                nhours = int(self.timeframe.replace('H', ''))
                delta = datetime.timedelta(hours=int(nhours))

        startO = pd.datetime.strptime(self.start, '%Y-%m-%d %H:%M:%S')
        endO = pd.datetime.strptime(self.end, '%Y-%m-%d %H:%M:%S')

        SRlst = None
        loop = 0
        tlist = []
        tend = None
        while startO <= endO:
            if tend is not None:
                # this means that there is currently an active trade
                if startO <= tend:
                    startO = startO + delta
                    continue
                else:
                    tend = None
            if self.settings.getboolean('general', 'debug') is True:
                print("[DEBUG] Trade bot - analyzing candle:{0}".format(startO.isoformat()))
            if loop == 0:
                SRlst = self.calc_SR(adateObj=startO)
                if self.settings.getboolean('general', 'debug') is True:
                    print("[DEBUG] Identified HAreaList for time {0}:".format(startO.isoformat()))
                    SRlst.print()
            elif loop == self.settings.getint('trade_bot',
                                              'period'):
                SRlst = self.calc_SR(adateObj=startO)
                if self.settings.getboolean('general', 'debug') is True:
                    print("[DEBUG] Identified HAreaList for time {0}:".format(startO.isoformat()))
                    SRlst.print()
                loop = 0
            oanda.run(start=startO.isoformat(),
                      count=1)

            candle_list = oanda.fetch_candleset()
            c_candle = candle_list[0] # this is the current candle that
                                      # is being checked

            #check if there is any HArea overlapping with c_candle
            HAreaSel = SRlst.onArea(candle=candle_list[0])

            if HAreaSel is not None:
                c_candle.set_candle_features()
                # guess the if trade is 'long' or 'short'
                type = self.__get_trade_type(ic=c_candle, harea_sel=HAreaSel, delta=delta)
                prepare_trade = False
                if c_candle.indecision_c(ic_perc=self.settings.getint('general', 'ic_perc')) is True:
                    prepare_trade = True
                elif type == 'short' and c_candle.colour == 'red':
                    prepare_trade = True
                elif type == 'long' and c_candle.colour == 'green':
                    prepare_trade =True

                if prepare_trade is True:
                    t = self.prepare_trade(type=type,
                                           ic=c_candle,
                                           harea_sel=HAreaSel,
                                           delta=delta)
                    t.run_trade(expires=1)
                    if t.entered is True:
                        tlist.append(t)
                        tend = t.end
            startO = startO+delta
            loop += 1
        if len(tlist) == 0:
            return None
        else:
            tl = TradeList(tlist=tlist,
                           settingf=self.settingf)
            return tl

    def __calc_diff(self, df_loc, increment_price):
        '''
        Function to select the best S/R for areas that
        are less than 3*increment_price

        Parameters
        ----------
        df_loc : Pandas dataframe with S/R areas
        increment_price : float

        Returns
        -------
        Pandas dataframe with selected S/R
        '''

        prev_price = None
        prev_row = None
        prev_ix = None
        tog_seen = False
        for index, row in df_loc.iterrows():
            if prev_price is None:
                prev_price = float(row['price'])
                prev_row = row
                prev_ix = index
            else:
                diff = round(float(row['price']) - prev_price, 4)
                if diff < 3 * increment_price:
                    tog_seen = True
                    if row['bounces'] <= prev_row['bounces'] and row['tot_score'] < prev_row['tot_score']:
                        # remove current row
                        df_loc.drop(index, inplace=True)
                    elif row['bounces'] >= prev_row['bounces'] and row['tot_score'] > prev_row['tot_score']:
                        # remove previous row
                        df_loc.drop(prev_ix, inplace=True)
                        prev_price = float(row['price'])
                        prev_row = row
                        prev_ix = index
                    elif row['bounces'] <= prev_row['bounces'] and row['tot_score'] > prev_row['tot_score']:
                        # remove previous row as scores in current takes precedence
                        df_loc.drop(prev_ix, inplace=True)
                        prev_price = float(row['price'])
                        prev_row = row
                        prev_ix = index
                    elif row['bounces'] >= prev_row['bounces'] and row['tot_score'] < prev_row['tot_score']:
                        # remove current row as scores in current takes precedence
                        df_loc.drop(index, inplace=True)
                    elif row['bounces'] == prev_row['bounces'] and row['tot_score'] == prev_row['tot_score']:
                        # exactly same quality for row and prev_row
                        # remove current arbitrarily
                        df_loc.drop(index, inplace=True)
                else:
                    prev_price = float(row['price'])
                    prev_row = row
                    prev_ix = index
        return df_loc, tog_seen

    def get_max_min(self, adateObj):
        '''
        Function to get the price range for identifying S/R by checking the max
        and min price for CandleList starting in
        'adateObj'- self.settings.getint('trade_bot', 'period_range') and ending in 'adateObj'

        Parameters
        ----------
        datetime object used for identifying
        S/R areas

        Returns
        -------
        max, min floats
        '''

        oanda = OandaAPI(instrument=self.pair,
                         granularity=self.timeframe,
                         settingf=self.settingf)

        delta_period = periodToDelta(self.settings.getint('trade_bot', 'period_range'),
                                     self.timeframe)
        delta_1 = periodToDelta(1, self.timeframe)

        start = adateObj - delta_period  # get the start datetime for this CandleList period
        end = adateObj + delta_1  # increase self.start by one candle to include self.start

        oanda.run(start=start.isoformat(),
                  end=end.isoformat())

        candle_list = oanda.fetch_candleset()
        cl = CandleList(candle_list,
                        instrument=self.pair,
                        id='test',
                        granularity=self.timeframe,
                        settingf=self.settingf)

        max = cl.get_highest()
        min = cl.get_lowest()

        # add a number of pips to max,min to be sure that we
        # also detect the extreme pivots
        max = add_pips2price(self.pair, max, self.settings.getint('trade_bot', 'add'))
        min = substract_pips2price(self.pair, min, self.settings.getint('trade_bot', 'add'))

        return max, min

    def calc_SR(self, adateObj):
        '''
        Function to calculate S/R lines

        Parameters
        ----------
        datetime object used for identifying
        S/R areas

        Return
        ------
        HAreaList object
        '''

        # calculate price range for calculating S/R
        ul, ll = self.get_max_min(adateObj)

        if self.settings.getboolean('general', 'debug') is True:
            print("[DEBUG] Running calc_SR for estimated range: {0}-{1}".format(ll, ul))

        prices = []
        bounces = []  # contains the number of pivots per price level
        score_per_bounce = []
        tot_score = []
        # the increment of price in number of pips is double the hr_extension
        prev_p = None
        p = float(ll)
        while p <= float(ul):
            if self.settings.getboolean('general', 'debug') is True:
                print("Processing S/R at {0}".format(round(p, 4)))
            # each of 'p' will become a S/R that will be tested for bounces
            # set entry to price+30pips
            entry = add_pips2price(self.pair, p, 30)
            # set S/L to price-30pips
            SL = substract_pips2price(self.pair, p, 30)
            t = Trade(
                id='{0}.{1}.detect_sr.{2}'.format(self.pair, adateObj.isoformat(), round(p, 5)),
                start=adateObj.strftime('%Y-%m-%d %H:%M:%S'),
                pair=self.pair,
                timeframe='D',
                type='short',
                entry=entry,
                SR=p,
                SL=SL,
                RR=1.5,
                strat='counter_b1',
                settingf=self.settingf)

            c = Counter(
                trade=t,
                init_feats=True,
                settingf=self.settingf
            )

            if len(c.pivots.plist) == 0:
                mean_pivot = 0
            else:
                mean_pivot = round(c.score_pivot, 2)

            prices.append(round(p, 5))
            bounces.append(len(c.pivots.plist))
            tot_score.append(c.total_score)
            score_per_bounce.append(mean_pivot)
            # increment price to following price
            p = add_pips2price(self.pair, p, 60)
            if prev_p is None:
                prev_p = p
            else:
                increment_price = round(p - prev_p, 5)
                prev_p = p

        data = {'price': prices,
                'bounces': bounces,
                'scores': score_per_bounce,
                'tot_score': tot_score}

        df = pd.DataFrame(data=data)
        ### establishing bounces threshold as the args.th quantile
        # selecting only rows with at least one pivot and tot_score>0,
        # so threshold selection considers only these rows
        # and selection is not biased when range of prices is wide
        dfgt1 = df.loc[(df['bounces'] > 0)]
        dfgt2 = df.loc[(df['tot_score'] > 0)]
        bounce_th = dfgt1.bounces.quantile(self.settings.getfloat('trade_bot', 'th'))
        score_th = dfgt2.tot_score.quantile(self.settings.getfloat('trade_bot', 'th'))
        if self.settings.getboolean('general', 'debug') is True:
            print("[DEBUG] Selected number of pivot threshold: {0}".format(bounce_th))
            print("[DEBUG] Selected tot score threshold: {0}".format(score_th))

        # selecting records over threshold
        dfsel = df.loc[(df['bounces'] > bounce_th) | (df['tot_score'] > score_th)]

        # repeat until no overlap between prices
        ret = self.__calc_diff(dfsel, increment_price)
        dfsel = ret[0]
        tog_seen = ret[1]
        while tog_seen is True:
            ret = self.__calc_diff(dfsel, increment_price)
            dfsel = ret[0]
            tog_seen = ret[1]

        # iterate over DF with selected SR to create a HAreaList
        halist = []
        for index, row in dfsel.iterrows():
            resist = HArea(price=row['price'],
                           pips=30,
                           instrument=self.pair,
                           granularity=self.timeframe,
                           no_pivots=row['bounces'],
                           tot_score=row['tot_score'],
                           settingf=self.settingf)
            halist.append(resist)

        halist = HAreaList(
            halist=halist,
            settingf="data/settings.ini"
        )

        return halist

