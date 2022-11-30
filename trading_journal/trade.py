from __future__ import division

import math
import logging
import datetime

from forex.pivot import PivotList
from forex.harea import HArea
from utils import *
from forex.params import trade_params
from api.oanda.connect import Connect

# create logger
t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)

class Trade(object):
    """This is the parent class represents a single row from the TradeJournal class.

    Class variables:
        entered: False if trade not taken (price did not cross self.entry). True otherwise
        start: Time/date when the trade was taken. i.e. 20-03-2017 08:20:00s
        pair: Currency pair used in the trade. i.e. AUD_USD
        timeframe: Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
        outcome: Outcome of the trade. Possible values are: success, failure, breakeven
        entry: entry price
        exit: exit price
        entry_time: Datetime for price reaching the entry price
        type: What is the type of the trade (long,short)
        SL:  float, Stop/Loss price
        TP:  float, Take profit price. If not defined then it will calculated by using the RR
        SR:  float, Support/Resistance area
        RR:  float, Risk Ratio
        pips:  Number of pips of profit/loss. This number will be negative if outcome was failure
        clist: CandleList object"""

    def __init__(self, init_clist:bool=False, **kwargs)->None:
        allowed_keys = ['entered', 'start', 'end', 'pair', 'timeframe', 'outcome', 'entry', 'exit', 
        'entry_time', 'type', 'SL', 'TP', 'SR', 'RR', 'pips', 'clist', 'strat']
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        if init_clist and not hasattr(self, 'clist'):
            self._init_clist()
        self.__dict__.update({'start' : try_parsing_date(self.__dict__['start'])})
        if hasattr(self, 'end'):
            self.__dict__.update({'end' : try_parsing_date(self.__dict__['end'])})
        self._validate_params()

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
    
    def _init_clist(self)->None:
        '''Init clist for this Trade'''
        conn = Connect(
            instrument=self.pair,
            granularity=self.timeframe)
        clO = conn.query(self.start, self.end)
        self.clist = clO

    def get_trend_i(self)->datetime:
        '''Function to calculate the start of the trend'''
        pvLst = PivotList(self.clist)
        merged_s = pvLst.calc_itrend()

        if self.type == "long":
            candle = merged_s.get_highest()
        elif self.type == "short":
            candle = merged_s.get_lowest()

        return candle.time

    def run_trade(self, expires: int=2)->None:
        '''Run the trade until conclusion from a start date.

        Arguments:
            expires : Number of candles after start datetime to check
                      for entry
        '''
        t_logger.info(f"Run run_trade with id: {self.pair}:{self.start}")

        entry = HArea(price=self.entry,
                      instrument=self.pair,
                      pips=trade_params.hr_pips,
                      granularity=self.timeframe)
        SL = HArea(price=self.SL,
                   instrument=self.pair,
                   pips=trade_params.hr_pips,
                   granularity=self.timeframe)
        TP = HArea(price=self.TP,
                   instrument=self.pair,
                   pips=trade_params.hr_pips,
                   granularity=self.timeframe)

        period = None
        if self.timeframe == "D":
            period = 24
        else:
            period = int(self.timeframe.replace('H', ''))

        # generate a range of dates starting at self.start and ending trade_params.numperiods later in order to assess the outcome
        # of trade and also the entry time
        self.start = datetime.strptime(str(self.start), '%Y-%m-%d %H:%M:%S')
        # date_list will contain a list with datetimes that will be used for running self
        date_list = [self.start + timedelta(hours=x*period) for x in range(0, trade_params.numperiods)]
        count = 0
        self.entered = False
        for d in date_list:
            count += 1
            if expires is not None:
                if count > expires and self.entered is False:
                    self.outcome = 'n.a.'
                    break
            cl = self.clist.fetch_by_time(d)
            if cl is None:
                continue
            if self.entered is False:
                entry_time = entry.get_cross_time(candle=cl,
                                                  granularity=trade_params.granularity)
                if entry_time != 'n.a.':
                    t_logger.info("Trade entered")
                    self.entry_time = entry_time.isoformat()
                    self.entered = True
            if self.entered is True:
                # will be n.a. if cl does not cross SL
                failure_time = SL.get_cross_time(candle=cl,
                                                 granularity=trade_params.granularity)
                # sometimes there is a jump in the price and SL is not crossed
                is_gap = False
                if (self.type == "short" and cl.l > SL.price) or\
                        (self.type == "long" and cl.h < SL.price):
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
                                                 granularity=trade_params.granularity)
                # sometimes there is a jump in the price and TP is not crossed
                is_gap = False
                if (self.type == "short" and cl.h < TP.price) or\
                        (self.type == "long" and cl.l > TP.price):
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

    def get_SLdiff(self)->float:
        """Function to calculate the difference in number of pips between the entry and
        the SL prices.

        Returns:
            number of pips
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

class cTrade(Trade):
    """This is subclass representing a Trade having a start and currently ongoing."""
    pass