from apis.oanda_api import OandaAPI
from configparser import ConfigParser
from trade_journal.trade import Trade
from trade_journal.trade_list import TradeList
from pattern.counter import Counter
from candle.candlelist import CandleList
from harea import HArea
from harea.harealist import HAreaList
from apis.ser_data_obj import ser_data_obj

from utils import *
import pandas as pd
import datetime
import re
import logging
import pickle

# create logger
tb_logger = logging.getLogger(__name__)
tb_logger.setLevel(logging.DEBUG)

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
    ser_data_f : str, Optional
                 ser_data file
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    settingf : str, Optional
               Path to *.ini file with settings
    '''
    def __init__(self, start, end, pair, timeframe, ser_data_f=None,
                 settingf=None, settings=None):
        self.start = start
        self.end = end
        self.pair = pair
        self.timeframe = timeframe
        self.ser_data_f = ser_data_f
        if ser_data_f is not None:
            self.ser_data_obj = ser_data_obj(ifile=ser_data_f)
        else:
            self.ser_data_obj = None

        self.settingf = settingf
        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

    def __get_trade_type(self, ic, delta):
        '''
        Function to guess what is the trade type (short or long)
        for this possible trade. It will also adjust the SL price
        to the most recent highest high/lowest low

        Parameters
        ----------
        ic : Candle object
             Indecision candle for this trade
        delta : Timedelta object corresponding to
                the time that needs to be increased

        Returns
        -------
        str: Trade type (long or short)
        float: adjusted SL
        '''

        oanda = OandaAPI(instrument=self.pair,
                         granularity=self.timeframe,
                         settingf=self.settingf,
                         settings=self.settings)

        # n x delta controls how many candles to go back in time
        # to check
        start = ic.time - 20*delta
        end = ic.time

        if self.ser_data_obj is None:
            tb_logger.info("Fetching data from API")
            oanda.run(start=start.isoformat(),
                      end=end.isoformat())
        else:
            tb_logger.info("Fetching data from File")
            oanda.data = self.ser_data_obj.slice(start=start,
                                                 end=end)

        candle_list = oanda.fetch_candleset()
        clObj = CandleList(candle_list,
                           instrument=self.pair,
                           id='fit_reg',
                           granularity=self.timeframe,
                           settingf=self.settingf,
                           settings=self.settings)
        # fit a regression line in order to check its slope
        # and guess the trade type
        (fitted_model, regression_model_mse) = clObj.fit_reg_line()

        slope = fitted_model.coef_[0][0]

        if slope < 0:
            type = 'long'
        elif slope > 0:
            type = 'short'

        # adjust SL
        if type == 'short':
            part = 'high{0}'.format(self.settings.get('general', 'bit'))
        elif type == 'long':
            part = 'low{0}'.format(self.settings.get('general', 'bit'))

        SL = None
        for c in reversed(candle_list):
            price = getattr(c, part)
            if SL is None:
                SL = price
                continue
            if type == 'short':
                if price > SL:
                    SL = price
            if type == 'long':
                if price < SL:
                    SL = price

        return type, SL

    def prepare_trade(self, type, SL, ic, harea_sel, delta):
        '''
        Prepare a Trade object
        and check if it is taken

        Parameters
        ----------
        type : str,
               Type of trade. 'short' or 'long'
        SL : float,
             Adjusted (by '__get_trade_type') SL price
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
            entry_p = getattr(ic, "low{0}".format(self.settings.get('general', 'bit')))
        elif type == 'long':
            # entry price will be the high of IC
            entry_p = getattr(ic, "high{0}".format(self.settings.get('general', 'bit')))
        startO = ic.time+delta
        t = Trade(
            id='{0}.bot'.format(self.pair),
            start=startO.strftime('%Y-%m-%d %H:%M:%S'),
            pair=self.pair,
            timeframe=self.timeframe,
            type=type,
            entry=entry_p,
            SR=harea_sel.price,
            SL=SL,
            RR=self.settings.getfloat('trade_bot', 'RR'),
            strat='counter',
            ser_data_obj=self.ser_data_obj,
            settingf=self.settingf,
            settings=self.settings)

        return t

    def run(self, discard_sat=True, pickled_file=None):
        '''
        This function will run the Bot from start to end
        one candle at a time

        Parameter
        ---------
        discard_sat : Bool
                      If this is set to True, then the Trade wil not
                      be taken if IC falls on a Saturday. Default: True
        pickled_file : str
                       Path used to dump the pickled representation of the dict
                       of HAreaList generated by store_SRlist (if self.settings.
                       getboolean('trade_bot', 'store_SRlist' is True
                       Or path used to load the pickled representation (if
                       self.settings.getboolean('trade_bot', 'load_SRlist' is
                       True)

        Returns
        -------
        TradeList object with Trades taken. None if no trades
        were taken
        '''
        tb_logger.info("Running...")

        oanda = OandaAPI(instrument=self.pair,
                         granularity=self.timeframe,
                         settingf=self.settingf,
                         settings=self.settings)
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

        dict_SRlist = {}
        if self.settings.getboolean('trade_bot', 'load_SRlist') is True:
            tb_logger.info("Loading dict of HAreaLists from pickled "
                           "file: {0}".format(pickled_file))
            pickled_fh = open(pickled_file, 'rb')
            dict_SRlist = pickle.load(pickled_fh)

        SRlst = None
        loop = 0
        tlist = []
        tend = None
        while startO <= endO:
            if tend is not None:
                # this means that there is currently an active trade
                if startO <= tend:
                    startO = startO + delta
                    loop += 1
                    continue
                else:
                    tend = None
            tb_logger.info("Trade bot - analyzing candle: {0}".format(startO.isoformat()))
            if loop == 0:
                # no iteration has occurred yet, so invoke .calc_SR for the first time
                if self.settings.getboolean('trade_bot', 'load_SRlist') is True:
                    SRlst= dict_SRlist[startO]
                else:
                    SRlst = self.calc_SR(adateObj=startO)
                res = SRlst.print()
                dict_SRlist[startO] = SRlst
                tb_logger.info("Identified HAreaList for time {0}:".format(startO.isoformat()))
                tb_logger.info("{0}".format(res))
            elif loop >= self.settings.getint('trade_bot',
                                              'period'):
                # An entire cycle has occurred. Invoke .calc_SR
                if self.settings.getboolean('trade_bot', 'load_SRlist') is True:
                    SRlst = dict_SRlist[startO]
                else:
                    SRlst = self.calc_SR(adateObj=startO)
                res = SRlst.print()
                dict_SRlist[startO] = SRlst
                tb_logger.info("Identified HAreaList for time {0}:".format(startO.isoformat()))
                tb_logger.info("{0}".format(res))
                loop = 0

            # fetch candle for current datetime
            if self.ser_data_obj is None:
                tb_logger.info("Fetching data from API")
                oanda.run(start=startO.isoformat(),
                          count=1)
            else:
                tb_logger.info("Fetching data from File")
                oanda.data = self.ser_data_obj.slice(start=startO,
                                                     count=1)

            candle_list = oanda.fetch_candleset()
            c_candle = candle_list[0] # this is the current candle that
                                      # is being checked

            # c_candle.time is not equal to startO
            # when startO is non-working day, for example
            delta1hr = datetime.timedelta(hours=1)
            if (c_candle.time != startO) and (abs(c_candle.time-startO) > delta1hr):
                loop += 1
                tb_logger.info("Analysed dt {0} is not the same than APIs returned dt {1}."
                               " Skipping...".format(startO, c_candle.time))
                startO = startO + delta
                continue

            #check if there is any HArea overlapping with c_candle
            HAreaSel, sel_ix = SRlst.onArea(candle=candle_list[0])

            if HAreaSel is not None:
                c_candle.set_candle_features()
                # guess the if trade is 'long' or 'short'
                type, SL = self.__get_trade_type(ic=c_candle, delta=delta)
                prepare_trade = False
                if c_candle.indecision_c(ic_perc=self.settings.getint('general', 'ic_perc')) is True:
                    prepare_trade = True
                elif type == 'short' and c_candle.colour == 'red':
                    prepare_trade = True
                elif type == 'long' and c_candle.colour == 'green':
                    prepare_trade = True

                # discard if IC falls on a Saturday
                if c_candle.time.weekday() == 5 and discard_sat is True:
                    tb_logger.info("Possible trade at {0} falls on Sat. Skipping...".format(c_candle.time))
                    prepare_trade = False

                if prepare_trade is True:
                    t = self.prepare_trade(
                        type=type,
                        SL=SL,
                        ic=c_candle,
                        harea_sel=HAreaSel,
                        delta=delta)
                    t.strat = 'counter'
                    t.tot_SR = len(SRlst.halist)
                    t.rank_selSR = sel_ix
                    # calculate t.entry-t.SL in number of pips
                    # and discard if it is over threshold
                    diff = abs(t.entry-t.SL)
                    number_pips = float(calculate_pips(self.pair, diff))
                    if number_pips > self.settings.getint('trade_bot', 'SL_width_pips'):
                        loop += 1
                        startO = startO + delta
                        continue
                    if self.settings.getboolean('trade_bot', 'run_trades') is True:
                        t.run_trade(expires=2)
                        if t.entered is True:
                            if not hasattr(t, 'end'):
                                tb_logger.info("Trade.end will be n.a. Check if this trade hit the SL/TP in"
                                               "the analysed timeframe. Skipping...")
                                tend = None
                            else:
                                tlist.append(t)
                                tend = t.end
                    else:
                        tlist.append(t)
            startO = startO+delta
            loop += 1

        tb_logger.info("Run done")

        if self.settings.getboolean('trade_bot', 'store_SRlist') is True:
            tb_logger.info("Dumping dict of HAreaLists to pickled "
                           "file: {0}".format(pickled_file))
            pickled_lst_f = open(pickled_file, 'wb')
            pickle.dump(dict_SRlist, pickled_lst_f)
            pickled_lst_f.close()

        if len(tlist) == 0:
            return None
        else:
            tl = TradeList(tlist=tlist,
                           settingf=self.settingf,
                           settings=self.settings,
                           ser_data_obj=self.ser_data_obj
                           )

            if self.settings.getboolean('trade_bot', 'run_trades') is True:
                # analyse trades
                tl.analyze()
            return tl

    def __calc_diff(self, df_loc, increment_price):
        '''
        Function to select the best S/R for areas that
        are less than 3*increment_price

        Parameters
        ----------
        df_loc : Pandas dataframe with S/R areas
        increment_price : float
                          This is the increment_price
                          between different price levels
                          in order to identify S/Rs

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
                         settingf=self.settingf,
                         settings=self.settings)

        delta_period = periodToDelta(self.settings.getint('trade_bot', 'period_range'),
                                     self.timeframe)
        delta_1 = periodToDelta(1, self.timeframe)

        start = adateObj - delta_period  # get the start datetime for this CandleList period
        end = adateObj + delta_1  # increase self.start by one candle to include self.start

        if self.ser_data_obj is None:
            tb_logger.info("Fetching data from API")
            oanda.run(start=start.isoformat(),
                      end=end.isoformat())
        else:
            tb_logger.info("Fetching data from File")
            oanda.data = self.ser_data_obj.slice(start=start,
                                                 end=end)
        candle_list = oanda.fetch_candleset()
        cl = CandleList(candle_list,
                        instrument=self.pair,
                        id='test',
                        granularity=self.timeframe,
                        settingf=self.settingf,
                        settings=self.settings)

        max = cl.get_highest()
        min = cl.get_lowest()

        # add a number of pips to max,min to be sure that we
        # also detect the extreme pivots
        max = add_pips2price(self.pair, max, self.settings.getint('trade_bot', 'add_pips'))
        min = substract_pips2price(self.pair, min, self.settings.getint('trade_bot', 'add_pips'))

        return max, min

    def __initclist(self, timeframe, end, pair):
        '''
        Private function to initialize the CandleList object that goes from trade.start
        to self.settings.getint('counter', 'period')

        Parameters
        ----------
        timeframe : Timeframe
        end : Datetime object that will be the end of this CandleList
        pair : pair

        Returns
        -------
        Candlelist or
        None if Oanda API query was not successful
        '''

        delta_period = periodToDelta(self.settings.getint('trade_bot', 'period_range'),
                                     timeframe)
        delta_1 = periodToDelta(1, timeframe)
        start = end - delta_period  # get the start datetime for this CandleList period
        end = end + delta_1  # increase end by one candle to include end

        tb_logger.debug("Fetching candlelist for period: {0}-{1}".format(start, end))

        oanda = OandaAPI(url=self.settings.get('oanda_api', 'url'),
                         instrument=pair,
                         granularity=timeframe,
                         settingf=self.settingf,
                         settings=self.settings)

        if self.ser_data_obj is None:
            tb_logger.info("Fetching data from API")
            resp = oanda.run(start=start.isoformat(),
                             end=end.isoformat())
        else:
            tb_logger.info("Fetching data from File")
            oanda.data = self.ser_data_obj.slice(start=start,
                                                 end=end)
            resp = 200

        if resp == 200:
            candle_list = oanda.fetch_candleset()

            cl = CandleList(candle_list,
                            settingf=self.settingf,
                            settings=self.settings,
                            instrument=pair,
                            granularity=timeframe,
                            ser_data_obj=self.ser_data_obj,
                            id="test",
                            type="short")
            cl.calc_rsi()
            return cl
        else:
            t_logger.warn("API query was not OK. No CandleList created ")
            return None

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
        tb_logger.info("Running calc_SR for estimated range: {0}-{1}".format(ll, ul))
        prices = []
        bounces = []  # contains the number of pivots per price level
        score_per_bounce = []
        tot_score = []
        # the increment of price in number of pips is double the hr_extension
        prev_p = None
        p = float(ll)

        cl = self.__initclist(timeframe=self.timeframe,
                              end=adateObj,
                              pair=self.pair)
        while p <= float(ul):
            tb_logger.debug("Processing S/R at {0}".format(round(p, 4)))
            # each of 'p' will become a S/R that will be tested for bounces
            # set entry to price+self.settings.getint('trade_bot','i_pips')
            entry = add_pips2price(self.pair, p, self.settings.getint('trade_bot', 'i_pips'))
            # set S/L to price-self.settings.getint('trade_bot','i_pips')
            SL = substract_pips2price(self.pair, p, self.settings.getint('trade_bot', 'i_pips'))
            t = Trade(
                id='{0}.{1}.detect_sr.{2}'.format(self.pair, adateObj.isoformat(), round(p, 5)),
                start=adateObj.strftime('%Y-%m-%d %H:%M:%S'),
                pair=self.pair,
                timeframe=self.timeframe,
                type='short',
                entry=entry,
                SR=p,
                SL=SL,
                RR=1.5,
                strat='counter_b1',
                settingf=self.settingf,
                settings=self.settings)

            c = Counter(
                trade=t,
                clist_period=cl,
                ser_data_obj=self.ser_data_obj,
                init_feats=True,
                settings=self.settings)

            if len(c.pivots.plist) == 0:
                mean_pivot = 0
            else:
                mean_pivot = round(c.score_pivot, 2)

            prices.append(round(p, 5))
            bounces.append(len(c.pivots.plist))
            tot_score.append(c.total_score)
            score_per_bounce.append(mean_pivot)
            # increment price to following price.
            # Because the increment is made in pips
            # it does not suffer of the JPY pairs
            # issue
            p = add_pips2price(self.pair, p, 2*self.settings.getint('trade_bot', 'i_pips'))
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

        print("Selected number of pivot threshold: {0}".format(bounce_th))
        print("Selected tot score threshold: {0}".format(score_th))

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
                           pips=self.settings.getint('pivots', 'hr_pips'),
                           instrument=self.pair,
                           granularity=self.timeframe,
                           no_pivots=row['bounces'],
                           tot_score=round(row['tot_score'], 5),
                           settingf=self.settingf,
                           settings=self.settings)
            halist.append(resist)

        halist = HAreaList(halist=halist,
                           settingf="data/settings.ini",
                           settings=self.settings)

        tb_logger.info("Run done")

        return halist

