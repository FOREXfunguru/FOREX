from __future__ import division

import math
import logging
import datetime as dt

from api.oanda.connect import Connect
from forex.candle.candlelist import CandleList
from forex.harea import HArea
from utils import *
from config import CONFIG

# create logger
t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)

class Trade(object):
    """This class represents a single row from the TradeJournal class

    Class variables
    ---------------
    entered: Boolean
             False if trade not taken (price did not cross self.entry). True otherwise
    start: datetime
           Time/date when the trade was taken. i.e. 20-03-2017 08:20:00s
    pair: Currency pair used in the trade. i.e. AUD_USD
    timeframe: Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    outcome: Outcome of the trade. Possible values are: success, failure, breakeven
    end: time/date when the trade ended. i.e. 20-03-2017 08:20:00
    entry: entry price
    exit: exit price
    entry_time: Datetime for price reaching the entry price
    type: What is the type of the trade (long,short)
    SL:  float, Stop/Loss price
    TP:  float, Take profit price. If not defined then it will calculated by using the RR
    SR:  float, Support/Resistance area
    RR:  float, Risk Ratio
    pips:  Number of pips of profit/loss. This number will be negative if outcome was failure"""

    def __init__(self, **kwargs)->None:
        allowed_keys = ['entered', 'start', 'pair', 'timeframe', 'outcome', 'end', 'entry', 'exit', 
        'entry_time', 'type', 'SL', 'TP', 'SR', 'RR', 'pips']
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        self._validate_params()
        self.type = type
        self.trend_i = self.get_trend_i()

    def _validate_params(self):
        if not hasattr(self, 'TP') and not hasattr(self, 'RR'):
            raise Exception("Neither the RR not "
                            "the TP is defined. Please provide RR")
        elif not hasattr(self, 'TP') and math.isnan(self.RR):
            raise Exception("Neither the RR not "
                            "the TP is defined. Please provide RR")
        elif hasattr(self, 'RR') and not math.isnan(self.RR):
            diff = (self.entry - self.SL) * self.RR
            self.TP = round(self.entry + diff, 4)

    def initclist(self):
        '''
        Function to initialize the CandleList object that goes from self.trade.start
        to CONFIG.getint('trade_bot', 'period_range')

        Returns
        -------
        CandleList
        '''
        delta_period = periodToDelta(CONFIG.getint('trade_bot', 'period_range'),
                                     self.timeframe)
        delta_1 = periodToDelta(1, self.timeframe)
        start = self.start - delta_period  # get the start datetime for this CandleList period
        end = self.start + delta_1  # increase self.start by one candle to include self.start
        if end > datetime.now():
            end = datetime.now().replace(microsecond=0)

        t_logger.debug("Fetching candlelist for period: {0}-{1}".format(start, end))

        conn = Connect(instrument=self.pair,
                       granularity=self.timeframe)

        ser_dir = None
        if CONFIG.has_option('general', 'ser_data_dir'):
            ser_dir = CONFIG.get('general', 'ser_data_dir')

        t_logger.debug("Fetching data")
        resp = conn.query(start=start.isoformat(),
                          end=end.isoformat(),
                          indir=ser_dir)

        cl = CandleList(resp, type=self.type)

        cl.calc_rsi()
        return cl

    def get_trend_i(self):
        '''
        Function to calculate the start of the trend

        Returns
        -------
        Datetime
        '''
        merged_s = self.period.calc_itrend()

        if self.type == "long":
            candle = merged_s.get_highest()
        elif self.type == "short":
            candle = merged_s.get_lowest()

        return candle['time']

    def fetch_candlelist(self):
        '''
        This function returns a CandleList object for this Trade

        Returns
        -------

        A CandleList object

        '''
        conn = Connect(instrument=self.pair,
                       granularity=self.timeframe)

        ser_dir = None
        if CONFIG.has_option('general', 'ser_data_dir'):
            ser_dir = CONFIG.get('general', 'ser_data_dir')

        if isinstance(self.start, datetime) is True:
            astart = self.start
        else:
            astart = try_parsing_date(self.start)

        if isinstance(self.end, datetime) is True:
            anend = self.end
        else:
            anend = try_parsing_date(self.end)

        t_logger.debug("Fetching data from API")
        res = conn.query(start=astart.isoformat(),
                         end=anend.isoformat(),
                         indir=ser_dir)

        cl = CandleList(res, type=self.type)
        return cl

    def run_trade(self, expires=2):
        '''
        Run the trade until conclusion from a start date

        Parameter
        ---------
        expires : int
                  Number of candles after start datetime to check
                  for entry. Default: 2
        '''

        t_logger.info("Run run_trade with id: {0}".format(self.id))

        entry = HArea(price=self.entry,
                      instrument=self.pair,
                      pips=CONFIG.getint('trade', 'hr_pips'),
                      granularity=self.timeframe)
        SL = HArea(price=self.SL,
                   instrument=self.pair,
                   pips=CONFIG.getint('trade', 'hr_pips'),
                   granularity=self.timeframe)
        TP = HArea(price=self.TP,
                   instrument=self.pair,
                   pips=CONFIG.getint('trade', 'hr_pips'),
                   granularity=self.timeframe)

        period = None
        if self.timeframe == "D":
            period = 24
        else:
            period = int(self.timeframe.replace('H', ''))

        # generate a range of dates starting at self.start and ending numperiods later in order to assess the outcome
        # of trade and also the entry time
        self.start = datetime.strptime(str(self.start), '%Y-%m-%d %H:%M:%S')
        numperiods = CONFIG.getint('trade', 'numperiods')
        # date_list will contain a list with datetimes that will be used for running self
        date_list = [datetime.strptime(str(self.start.isoformat()), '%Y-%m-%dT%H:%M:%S')
                     + timedelta(hours=x*period) for x in range(0, numperiods)]

        conn = Connect(instrument=self.pair,
                       granularity=self.timeframe)

        ser_dir = None
        if CONFIG.has_option('general', 'ser_data_dir'):
            ser_dir = CONFIG.get('general', 'ser_data_dir')
        count = 0
        self.entered = False
        for d in date_list:
            count += 1
            if expires is not None:
                if count > expires and self.entered is False:
                    self.outcome = 'n.a.'
                    break
            t_logger.debug("Fetching data from API")
            res = conn.query(start=d.isoformat(),
                             count=1,
                             indir=ser_dir)
            cl = res['candles'][0]
            if self.entered is False:
                entry_time = entry.get_cross_time(candle=cl,
                                                  granularity=CONFIG.get('trade', 'granularity'))
                if entry_time != 'n.a.':
                    t_logger.info("Trade entered")
                    self.entry_time = entry_time.isoformat()
                    self.entered = True
            if self.entered is True:
                # will be n.a. is cl does not cross SL
                failure_time = SL.get_cross_time(candle=cl,
                                                 granularity=CONFIG.get('trade', 'granularity'))
                # sometimes there is a jump in the price and SL is not crossed
                is_gap = False
                if (self.type == "short" and cl['lowAsk'] > SL.price) or\
                        (self.type == "long" and cl['highAsk'] < SL.price):
                    is_gap = True
                    failure_time = d
                if (failure_time is not None and failure_time != 'n.a.') or is_gap is True:
                    self.outcome = 'failure'
                    self.end = failure_time
                    self.exit = SL.price
                    self.pips = float(calculate_pips(self.pair, abs(self.SL-self.entry)))*-1
                    t_logger.info("S/L was hit")
                    break
                # will be n.a. if cl does not cross TP
                success_time = TP.get_cross_time(candle=cl,
                                                 granularity=CONFIG.get('trade', 'granularity'))
                # sometimes there is a jump in the price and TP is not crossed
                is_gap = False
                if (self.type == "short" and cl['highAsk'] < TP.price) or\
                        (self.type == "long" and cl['lowAsk'] > TP.price):
                    is_gap = True
                    success_time = d
                if (success_time is not None and success_time !='n.a.') or is_gap is True:
                    self.outcome = 'success'
                    t_logger.info("T/P was hit")
                    self.end = success_time
                    self.exit = TP.price
                    self.pips = float(calculate_pips(self.pair, abs(self.TP - self.entry)))
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

        return number_pips

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
