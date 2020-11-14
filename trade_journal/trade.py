from __future__ import division

import math
import warnings
import pdb
import logging
import datetime as dt

from apis.oanda_api import OandaAPI
from candle.candlelist import CandleList
from harea.harea import HArea
from utils import *
from configparser import ConfigParser

# create logger
t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)

class Trade(object):
    '''
    This class represents a single row from the dataframe in the trade_journal class

    Class variables
    ---------------

    entered: Boolean, Optional
             False if trade not taken (price did not cross self.entry). True otherwise
             Default : False
    trend_i: datetime, Optional
             start of the trend
    start: datetime, Required
           Time/date when the trade was taken. i.e. 20-03-2017 08:20:00s
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    outcome: str, Optional
             Outcome of the trade. Possible values are: success, failure, breakeven
    end: datetime, Optional
         Time/date when the trade ended. i.e. 20-03-2017 08:20:00
    entry: float, Optional
           entry price
    entry_time: datetime.optional
                Datetime for price reaching the entry price
    type: str, Optional
          What is the type of the trade (long,short)
    SL:  float, Optional
         Stop/Loss price
    TP:  float, Optional
         Take profit price. If not defined then it will calculated by using the RR
    SR:  float, Optional
         Support/Resistance area
    RR:  float, Optional
         Risk Ratio
    pips:  int, Optional
           Number of pips of profit/loss. This number will be negative if outcome was failure
    strat: string, Required
           What strategy was used for this trade.
    id : str, Required
         Id used for this object
    SLdiff : float, Optional
             Diff in pips between entry and SL
    tot_SR : int, Optional
             Number of SR areas identified for this Trade
    rank_selSR : int, Optional
                 Position in the HArea list for selected SR. Where 0 is the rank for the
                 lowest HArea.price
    settingf : str, Optional
               Path to *.ini file with settings
    settings : ConfigParser object generated using 'settingf'
               Optional
    ser_data_obj : ser_data_obj, Optional
                   ser_data_obj with serialized data
    '''

    def __init__(self, strat, start, type=None, tot_SR=None, rank_selSR=None,
                 settingf=None, settings=None, ser_data_obj=None, entered=False, **kwargs):
        self.__dict__.update(kwargs)
        if not hasattr(self, 'TP') and not hasattr(self, 'RR'):
            raise Exception("Neither the RR not "
                            "the TP is defined. Please provide RR")
        elif not hasattr(self, 'TP') and math.isnan(self.RR):
            raise Exception("Neither the RR not "
                            "the TP is defined. Please provide RR")
        elif hasattr(self, 'RR') and not math.isnan(self.RR):
            diff = (self.entry - self.SL) * self.RR
            self.TP = round(self.entry + diff, 4)

        self.strat = strat
        self.start = datetime.strptime(start,
                                      '%Y-%m-%d %H:%M:%S')
        self.pair = re.sub('/', '_', self.pair)
        self.pair = re.sub('.bot', '', self.pair)
        self.strat = strat
        self.tot_SR = tot_SR
        self.ser_data_obj = ser_data_obj
        self.rank_selSR = rank_selSR
        #remove potential whitespaces in timeframe
        self.timeframe = re.sub(' ', '', self.timeframe)
        self.settingf = settingf
        self.entered = entered
        self.type = type

        # calculate SLdiff
        self.SLdiff = self.get_SLdiff()

        # parse settings file (in .ini file)
        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

    def fetch_candlelist(self):
        '''
        This function returns a CandleList object for this Trade

        Returns
        -------

        A CandleList object

        '''
        oanda = OandaAPI(instrument=self.pair,
                         granularity=self.timeframe,
                         settingf=self.settingf,
                         settings=self.settings)

        if isinstance(self.start, datetime) is True:
            astart = self.start
        else:
            astart = try_parsing_date(self.start)

        if isinstance(self.end, datetime) is True:
            anend = self.end
        else:
            anend = try_parsing_date(self.end)

        if self.ser_data_obj is None:
            t_logger.debug("Fetching data from API")
            oanda.run(start=astart.isoformat(),
                      end=anend.isoformat())
        else:
            t_logger.debug("Fetching data from File")
            oanda.data = self.ser_data_obj.slice(start=astart,
                                                 end=anend)

        candle_list = oanda.fetch_candleset()
        cl = CandleList(candle_list,
                        type=self.type,
                        settingf=self.settingf,
                        settings=self.settings)

        return cl

    def calc_trade_session(self):
        '''
        Function to calculate the trade session (European, Asian,
        NAmerican) the trade was taken

        Returns
        -------
        str Comma-separated string with different sessions: i.e. european,asian
                                                                 or namerican, etc...
        I will return n.a. if self.entry_time is not defined
        '''
        if not hasattr(self, 'entry_time'):
            return "n.a."
        dtime = datetime.strptime(self.entry_time, '%Y-%m-%dT%H:%M:%S')
        # define the different sessions time boundaries
        a_u2 = dt.time(int(7), int(0), int(0))
        a_l2 = dt.time(int(0), int(0), int(0))
        a_u1 = dt.time(int(23), int(59), int(59))
        a_l1 = dt.time(int(23), int(0), int(0))
        e_u = dt.time(int(15), int(0), int(0))
        e_l = dt.time(int(7), int(0), int(0))
        na_u = dt.time(int(19), int(0), int(0))
        na_l = dt.time(int(12), int(0), int(0))

        sessions = []
        session_seen = False
        if dtime.time() >= a_l1 and dtime.time() <= a_u1:
            sessions.append('asian')
            session_seen = True
        if dtime.time() >= a_l2 and dtime.time() <= a_u2:
            sessions.append('asian')
            session_seen = True
        if dtime.time() >= e_l and dtime.time() <= e_u:
            sessions.append('european')
            session_seen = True
        if dtime.time() >= na_l and dtime.time() <= na_u:
            sessions.append('namerican')
            session_seen = True
        if session_seen is False:
            sessions.append('nosession')
        return ",".join(sessions)

    def run_trade(self, expires=None):
        '''
        Run the trade until conclusion from a start date
        '''

        t_logger.info("Run run_trade with id: {0}".format(self.id))

        entry = HArea(price=self.entry,
                      instrument=self.pair,
                      pips=self.settings.getint('trade', 'hr_pips'),
                      granularity=self.timeframe,
                      ser_data_obj=None,
                      settings=self.settings)
        SL = HArea(price=self.SL,
                   instrument=self.pair,
                   pips=self.settings.getint('trade', 'hr_pips'),
                   granularity=self.timeframe,
                   ser_data_obj=None,
                   settings=self.settings)
        TP = HArea(price=self.TP,
                   instrument=self.pair,
                   pips=self.settings.getint('trade', 'hr_pips'),
                   granularity=self.timeframe,
                   ser_data_obj=None,
                   settings=self.settings)

        period = None
        if self.timeframe == "D":
            period = 24
        else:
            period = int(self.timeframe.replace('H', ''))

        # generate a range of dates starting at self.start and ending numperiods later in order to assess the outcome
        # of trade and also the entry time

        self.start = datetime.strptime(str(self.start), '%Y-%m-%d %H:%M:%S')
        numperiods = self.settings.getint('trade', 'numperiods')
        # date_list will contain a list with datetimes that will be used for running self
        date_list = [datetime.strptime(str(self.start.isoformat()), '%Y-%m-%dT%H:%M:%S')
                     + timedelta(hours=x*period) for x in range(0, numperiods)]

        count = 0
        self.entered = False
        for d in date_list:
            count += 1
            if expires is not None:
                if count > expires and self.entered is False:
                    self.outcome = 'n.a.'
                    break
            oanda = OandaAPI(instrument=self.pair,
                             granularity=self.timeframe,
                             settingf=self.settingf,
                             settings=self.settings)

            if self.ser_data_obj is None:
                t_logger.debug("Fetching data from API")
                oanda.run(start=d.isoformat(),
                          count=1)
            else:
                t_logger.debug("Fetching data from File")
                oanda.data = self.ser_data_obj.slice(start=d,
                                                     count=1)

            cl = oanda.fetch_candleset()[0]
            if self.entered is False:
                entry_time = entry.get_cross_time(candle=cl,
                                                  granularity=self.settings.get('trade', 'granularity'))
                if entry_time != 'n.a.':
                    t_logger.info("Trade entered")
                    # modify self.start to the datetime
                    # that Trade has actually entered
                    self.start = d
                    self.entry_time = entry_time.isoformat()
                    self.entered = True
            if self.entered is True:
                # will be n.a. is cl does not cross SL
                failure_time = SL.get_cross_time(candle=cl,
                                                 granularity=self.settings.get('trade', 'granularity'))
                # sometimes there is a jump in the price and SL is not crossed
                is_gap = False
                if (self.type == "short" and cl.lowAsk > SL.price) or (self.type == "long" and cl.highAsk < SL.price):
                    is_gap = True
                    failure_time = d
                if (failure_time is not None and failure_time != 'n.a.') or is_gap is True:
                    self.outcome = 'failure'
                    self.end = failure_time
                    self.pips = float(calculate_pips(self.pair,abs(self.SL-self.entry)))*-1
                    t_logger.info("S/L was hit")
                    break
                # will be n.a. if cl does not cross TP
                success_time = TP.get_cross_time(candle=cl,
                                                 granularity=self.settings.get('trade', 'granularity'))
                # sometimes there is a jump in the price and TP is not crossed
                is_gap = False
                if (self.type == "short" and cl.highAsk < TP.price) or (self.type == "long" and cl.lowAsk > TP.price):
                    is_gap = True
                    success_time = d

                if (success_time is not None and success_time !='n.a.') or is_gap is True:
                    self.outcome = 'success'
                    t_logger.info("T/P was hit")
                    self.end = success_time
                    self.pips = float(calculate_pips(self.pair,
                                                     abs(self.TP - self.entry)))
                    break
        try:
            assert getattr(self, 'outcome')
        except:
            t_logger.warning("No outcome could be calculated")
            self.outcome = "n.a."
            self.pips = 0

        t_logger.info("Done run_trade")

    def get_SLdiff(self):
        """
        Function to calculate the difference in number of pips between the entry and
        the SL prices

        Returns
        -------
        float with pips
        """

        diff = abs(self.entry - self.SL)
        number_pips = float(calculate_pips(self.pair, diff))

        self.SLdiff = number_pips

        return number_pips

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
