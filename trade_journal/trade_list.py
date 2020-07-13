from configparser import ConfigParser
from pattern.counter import Counter

import pdb
import logging
import datetime
import math

# create logger
tl_logger = logging.getLogger(__name__)
tl_logger.setLevel(logging.DEBUG)

class TradeList(object):
    '''
    Class that represents a list of Trade objects

    Class variables
    ---------------
    tlist : list, Required
            List of Trade objects
    settingf : str, Optional
               Path to *.ini file with settings
    settings : ConfigParser object generated using 'settingf'
               Optional
    ser_data_obj : ser_data_obj, Optional
                   ser_data_obj with serialized data
    '''

    def __init__(self, tlist, settingf=None, settings=None, ser_data_obj=None):
        self.settingf = settingf
        self.tlist = tlist
        self.ser_data_obj = ser_data_obj

        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

    def analyze(self):
        '''
        Analyze each of the Trade objects in TradeList depending
        on value of settings.get('counter', 'strats') and add the
        calculated attributes to Trade

        :returns
        TradeList
        '''

        #these are the strategies that will be analysed using the Counter pattern
        tl_logger.info("Strategies that will be analysed: {0}".format(self.settings.get('counter', 'strats')))
        strats = self.settings.get('counter', 'strats').split(",")

        trade_list = []
        for t in self.tlist:
            tl_logger.info("Processing trade: {0}-{1}".format(t.pair, t.start))
            if t.strat in strats:
                if t.entered is False and (not hasattr(t, 'outcome') or math.isnan(t.outcome) is True):
                    t.run_trade()
                c = Counter(trade=t,
                            settingf=self.settingf,
                            settings=self.settings,
                            ser_data_obj=self.ser_data_obj,
                            init_feats=True)
                tl_logger.debug("Counter attributes analysed:{0}".format(self.settings.get('counter', 'attrbs').split(",")))
                attrb_ls = self.settings.get('counter', 'attrbs').split(",")
                for a in attrb_ls:
                    if hasattr(c, a) is True:
                        # add 'a' attribute to Trade object
                        setattr(t, a, getattr(c, a))
                    else:
                        tl_logger.warn("Attribute {0} is not defined in Counter object. Skipping...".format(a))
                        setattr(t, a, "n.a.")
            else:
                tl_logger.debug("Trade.strat ({0}) is not within list of trades to analyse. Skipping...".format(t.strat))
            trade_list.append(t)
            tl_logger.info("Done")
        tl = TradeList(settingf=self.settingf,
                       settings=self.settings,
                       tlist=trade_list)

        return tl

    def win_rate(self, strats):
        '''
        Calculate win rate and pips balance
        for this TradeList. If outcome attrb is not
        defined then it will invoke the run_trade method
        on each particular trade

        Parameters
        ----------
        strats : str
                 Comma-separated list of strategies to analyse: i.e. counter,counter_b1

        :return:
        int : number of successes
        int : number of failures
        pips : pips balance in this TradeList
        '''

        strat_l = strats.split(",")
        number_s = 0
        number_f = 0
        tot_pips = 0
        for t in self.tlist:
            if t.strat not in strat_l:
                continue
            if not hasattr(t, 'outcome'):
                t.run_trade()
            if t.outcome == 'success':
                number_s += 1
            elif t.outcome == 'failure':
                number_f += 1
            tot_pips += t.pips
        tot_pips = round(tot_pips, 2)
        tot_trades = number_s+number_f
        perc_wins = round(number_s*100/tot_trades, 2)
        perc_losses = round(number_f*100/tot_trades, 2)
        print("Tot number of trades: {0}\n-------------".format(tot_trades))
        print("Win trades: {0}; Loss trades: {1}".format(number_s, number_f))
        print("% win trades: {0}; % loss trades: {1}".format(perc_wins, perc_losses))
        print("Pips balance: {0}".format(tot_pips))

        return number_s, number_f, tot_pips



