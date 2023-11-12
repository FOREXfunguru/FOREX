from __future__ import division

import logging
import pdb

from datetime import datetime, timedelta
from forex.pivot import PivotList
from forex.harea import HArea
from forex.candle import Candle
from utils import (
    calculate_pips,
    add_pips2price,
    try_parsing_date,
    substract_pips2price,
    periodToDelta)
from utils import calculate_profit
from params import trade_params
from api.oanda.connect import Connect

# create logger
t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)

# Allowed Trade class attribures
ALLOWED_ATTRBS = ['entered', 'start', 'end', 'pair',
                  'timeframe', 'outcome', 'exit', 'entry_time', 'type',
                  'SR', 'RR', 'pips', 'clist', 'strat',
                  'tot_SR', 'rank_selSR']


class Trade(object):
    """This is the parent class represents a single row from the TradeJournal
       class.

    Class variables:
        entered: False if trade not taken (price did not cross self.entry).
                 True otherwise
        start: Time/date when the trade was taken
        pair: Currency pair used in the trade
        timeframe: Timeframe used for the trade.
        outcome: Outcome of the trade.
        entry: HArea representing the entry
        exit: exit price
        type: What is the type of the trade (long,short)
        SR:  Support/Resistance area
        RR:  Risk Ratio
        pips:  Number of pips of profit/loss. This number will be negative if
               outcome was failure
        clist: CandleList for this trade"""
    def __preinit__(self):
        if self.init_clist and not hasattr(self, 'clist'):
            self.init_clist()
        self.__dict__.update({'start':
                              try_parsing_date(self.__dict__['start'])})
        if hasattr(self, 'end') and isinstance(self.end, datetime):
            self.__dict__.update({'end':
                                  try_parsing_date(self.__dict__['end'])})

    def __init__(self,
                 entry: float,
                 SL: float,
                 TP: float = None,
                 **kwargs) -> None:
        self.__dict__.update((k, v) for k, v in kwargs.items()
                             if k in ALLOWED_ATTRBS)
        self.__preinit__()
        self.entry = entry
        self.SL = SL
        if kwargs.get("RR") is None and TP is None:
            raise ValueError("Neither the RR not "
                             "the TP is defined. Please provide at least one!")
        if kwargs.get("RR") is not None and TP is None:
            TP = self._calc_TP(RR=kwargs.get("RR"))
        elif kwargs.get("RR") is None and TP is not None:
            RR = self._calc_RR(TP=TP)
            self.RR = RR
        self.TP = TP
        self.SLdiff = self.get_SLdiff()
        self.entered = False

    @property
    def SL(self):
        return self._SL

    @SL.setter
    def SL(self, price: float):
        """HArea representing the SL price"""
        harea_obj = HArea(price=price,
                          instrument=self.pair,
                          pips=trade_params.hr_pips,
                          granularity=self.timeframe)
        self._SL = harea_obj

    @property
    def entry(self):
        return self._entry

    @entry.setter
    def entry(self, price: float):
        """HArea representing the entry price"""
        harea_obj = HArea(price=price,
                          instrument=self.pair,
                          pips=trade_params.hr_pips,
                          granularity=self.timeframe)
        self._entry = harea_obj

    @property
    def TP(self):
        return self._TP

    @TP.setter
    def TP(self, price: float):
        """HArea representing the TP price"""

        harea_obj = HArea(price=price,
                          instrument=self.pair,
                          pips=trade_params.hr_pips,
                          granularity=self.timeframe)
        self._TP = harea_obj

    def _calc_TP(self, RR: float) -> float:
        diff = (self.entry.price - self.SL.price) * self.RR
        return round(self.entry.price + diff, 4)

    def _calc_RR(self, TP: float) -> float:
        RR = abs(TP-self.entry.price)/abs(self.SL.price-self.entry.price)
        return round(RR, 2)

    def _calc_period(self) -> int:
        """Calculate number of hours for each period
        depending on the timeframe"""
        period = None
        if self.timeframe == "D":
            period = 24
        else:
            period = int(self.timeframe.replace('H', ''))
        return period

    def init_clist(self) -> None:
        """Init clist for this Trade"""
        delta = periodToDelta(trade_params.trade_period, self.timeframe)
        start = self.start
        if not isinstance(start, datetime):
            start = try_parsing_date(start)
        nstart = start - delta

        conn = Connect(
            instrument=self.pair,
            granularity=self.timeframe)
        clO = conn.query(nstart.isoformat(), start.isoformat())
        self.clist = clO

    def get_trend_i(self) -> datetime:
        """Function to calculate the start of the trend"""
        pvLst = PivotList(self.clist)
        merged_s = pvLst.calc_itrend()

        if self.type == "long":
            candle = merged_s.get_highest()
        elif self.type == "short":
            candle = merged_s.get_lowest()

        return candle.time

    def _adjust_tp(self) -> float:
        """Adjust TP when trade_params.strat==exit early"""
        tp_pips = float(calculate_pips(self.pair, self.TP))
        entry_pips = float(calculate_pips(self.pair, self.entry))
        diff = abs(tp_pips-entry_pips)
        tp_pips = trade_params.reduce_perc*diff/100
        if self.type == "long":
            new_tp = add_pips2price(self.pair, self.entry, tp_pips)
        else:
            new_tp = substract_pips2price(self.pair, self.entry, tp_pips)
        return new_tp

    def _fetch_candle(self, d: datetime) -> Candle:
        """Private method to query the API to get a single candle
        if it is not defined in self.clist.

        It will return None if market is closed
        """
        conn = Connect(
            instrument=self.pair,
            granularity=self.timeframe)
        clO = conn.query(start=d.isoformat(), end=d.isoformat())
        if len(clO.candles) == 1:
            return clO.candles[0]
        elif len(clO.candles) > 1:
            raise Exception("No valid number of candles in "
                            "CandleList")

    def _check_candle_overlap(self, cl: Candle, price: float) -> bool:
        """Method to check if Candle 'cl' overlaps 'price'"""
        return cl.l <= price <= cl.h

    def _end_trade(self,
                   connect: bool,
                   cl: Candle,
                   harea: HArea) -> None:
        """End trade"""
        end = None
        if connect is True:
            end = (harea.get_cross_time(candle=cl,
                   granularity=trade_params.granularity))
        else:
            end = cl.time
        self.end = end
        self.exit = harea.price

    def _finalise_trade(self, connect: bool, cl: Candle):
        if self.outcome == "success":
            price1 = self.TP.price
            self._end_trade(connect=connect,
                            cl=cl,
                            harea=self.TP)
        if self.outcome == "failure":
            price1 = self.SL.price
            self._end_trade(connect=connect,
                            cl=cl,
                            harea=self.SL)
        if self.outcome == "n.a.":
            price1 = cl.c
        self.pips = calculate_profit(prices=(price1,
                                             self.entry.price),
                                     type=self.type,
                                     pair=self.pair)

    def run_trade(self, expires: int = 2, connect=True) -> None:
        """Run the trade until conclusion from a start date.

        Arguments:
            expires : Number of candles after start datetime to check
                      for entry
        """
        t_logger.info(f"Run run_trade with id: {self.pair}:{self.start}")

        # Generate a range of dates starting at self.start and ending
        # trade_params.interval later in order to assess the outcome
        # of trade and also the entry time
        date_list = [self.start + timedelta(hours=x*self._calc_period())
                     for x in range(0, trade_params.interval)]
        count = 0
        self.entered = False
        for d in date_list:
            dtnow = datetime.now()
            if d.weekday() == 5:
                continue
            count += 1
            if (count > expires or d > dtnow) and self.entered is False:
                t_logger.warning("Trade entry expired or is in the future!")
                self.outcome = "n.a."
                self.pips = 0
                return
            cl = self.clist[d]
            if cl is None:
                if connect is True:
                    cl = self._fetch_candle(d=d)
                if cl is None:
                    count -= 1
                    continue
            if self.entered is False:
                if self._check_candle_overlap(cl, self.entry.price):
                    t_logger.info("Trade entered")
                    self.entered = True
                    if connect is True:
                        try:
                            entry_time = (self.entry.get_cross_time(candle=cl,
                                          granularity=trade_params.granularity))
                            self.entry_time = entry_time.isoformat()
                        except BaseException:
                            self.entry_time = cl.time.isoformat()
                    else:
                        self.entry_time = cl.time.isoformat()
            if self.entered is True:
                if self._check_candle_overlap(cl, self.SL.price):
                    t_logger.info("Sorry, SL was hit!")
                    self.outcome = "failure"
                if self._check_candle_overlap(cl, self.TP.price):
                    t_logger.info("Great, TP was hit!")
                    self.outcome = "success"
                if count >= trade_params.numperiods:
                    t_logger.warning("No outcome could be calculated in the "
                                     "trade_params.numperiods interval")
                    self.outcome = "n.a."

                if hasattr(self, 'outcome'):
                    self._finalise_trade(connect=connect, cl=cl)
                    return
        t_logger.info("Done run_trade")

    def get_SLdiff(self) -> float:
        """Function to calculate the difference in number of pips between the
        entry and the SL prices.

        Returns:
            number of pips
        """
        diff = abs(self.entry.price - self.SL.price)
        number_pips = float(calculate_pips(self.pair, diff))

        return number_pips

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append(f"{key}='{self.__dict__[key]}'")
        return ', '.join(sb)

    def __repr__(self):
        return "Trade"
