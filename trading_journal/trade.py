from __future__ import division

import logging
import pdb

from trading_journal.constants import ALLOWED_ATTRBS, VALID_TYPES
from datetime import datetime, timedelta
from forex.pivot import PivotList
from forex.harea import HArea
from forex.candle import Candle, CandleList
from utils import (
    calculate_pips,
    add_pips2price,
    try_parsing_date,
    substract_pips2price,
    periodToDelta)
from utils import calculate_profit
from params import trade_params
from api.oanda.connect import Connect

t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)


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
        clist: CandleList for this trade
        clist_tm: CandleList for trade management
        """
    def __preinit__(self):
        if not hasattr(self, "clist"):
            self.clist = self.init_clist(self.timeframe)
        if not hasattr(self, "clist_tm"):
            self.clist_tm = self.init_clist(trade_params.clisttm_tf)
        if self.clist_tm.instrument != self.clist_tm.instrument:
            raise ValueErrror("Inconsistent instruments between 'clist' and 'clist_tm'")

        self.__dict__.update({"start":
                              try_parsing_date(self.__dict__["start"])})
        if hasattr(self, "end"):
            self.__dict__.update({"end":
                                  try_parsing_date(self.__dict__["end"])})

    def _init_harea(self, price: float) -> HArea:
        harea_obj = HArea(price=price,
                          instrument=self.pair,
                          pips=trade_params.hr_pips,
                          granularity=self.timeframe)
        return harea_obj

    def __init__(self,
                 entry: float,
                 SL: float,
                 TP: float = None,
                 **kwargs) -> None:
        self.__dict__.update((k, v) for k, v in kwargs.items()
                             if k in ALLOWED_ATTRBS)
        self.__preinit__()
        self.entry = self._init_harea(entry) if not isinstance(entry, HArea) else entry
        self.SL = self._init_harea(SL) if not isinstance(SL, HArea) else SL
        if kwargs.get("RR") is None and TP is None:
            raise ValueError("Neither the RR not "
                             "the TP is defined. Please provide at least one!")
        if kwargs.get("RR") is not None and TP is None:
            TP = self._calc_TP(RR=kwargs.get("RR"))
        elif kwargs.get("RR") is None and TP is not None:
            RR = self._calc_RR(TP=TP)
            self.RR = RR
        self.TP = self._init_harea(TP) if not isinstance(TP, HArea) else TP
        self.SLdiff = self.get_SLdiff()
        self.entered = False

    def _calc_TP(self, RR: float) -> float:
        diff = (self.entry.price - self.SL.price) * self.RR
        return round(self.entry.price + diff, 4)

    def _calc_RR(self, TP: float) -> float:
        RR = abs(TP-self.entry.price)/abs(self.SL.price-self.entry.price)
        return round(RR, 2)

    def _calc_period(self) -> int:
        """Number of hours for period"""
        return 24 if self.timeframe == "D" else int(self.timeframe.replace("H",
                                                                           ""))

    def init_clist(self, timeframe: str) -> CandleList:
        delta = periodToDelta(trade_params.trade_period, timeframe)
        start = self.start
        if not isinstance(start, datetime):
            start = try_parsing_date(start)
        nstart = start - delta

        conn = Connect(
            instrument=self.pair,
            granularity=timeframe)
        clO = conn.query(nstart.isoformat(), start.isoformat())
        return clO

    def get_trend_i(self) -> datetime:
        """Function to calculate the start of the trend"""
        pvLst = PivotList(self.clist)
        merged_s = pvLst.calc_itrend()

        if self.type == "long":
            candle = merged_s.get_highest()
        elif self.type == "short":
            candle = merged_s.get_lowest()

        return candle.time

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

    def gen_datelist(self) -> list[datetime]:
        """Generate a range of dates starting at self.start and ending
        trade_params.interval later in order to assess the outcome
        of trade and also the entry time.
        """
        return [self.start + timedelta(hours=x*self._calc_period())
                for x in range(0, trade_params.interval)]

    def run_trade(self, expires: int = 2, connect=True) -> None:
        """Run the trade until conclusion from a start date.

        Arguments:
            expires: Number of candles after start datetime to check
                      for entry
            connect: If True then it will use the API to fetch candles
        """
        t_logger.info(f"Run run_trade with id: {self.pair}:{self.start}")

        count = 0
        self.entered = False
        for d in self.gen_datelist():
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
                if trade_params.strat not in VALID_TYPES:
                    raise ValueError(f"Unrecognised type: {type}")
                managed_trade =  None
                if trade_params.strat == "area_unaware":
                    managed_trade = UnawareTrade(**self.__dict__)
                    managed_trade.run_trade()
                    self.outcome = managed_trade.outcome
                    self.pips = managed_trade.pips
                    self.end = managed_trade.end
                    break
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


class UnawareTrade(Trade):
    """Class to represent an open Trade of the 'area_unaware' type"""

    preceding_candles = []

    def __init__(self,
                 candle_number: int = 3,
                 **kwargs):
        """Constructor

        Arguments:
            candle_number: number of candles against the trade to consider
        """
        self.candle_number = candle_number
        super().__init__(**kwargs)

    def check_if_against(self):
        """Function to check if middle_point values are
        agaisnt the trade
        """
        prices = [x.middle_point() for x in UnawareTrade.preceding_candles]
        if self.type == "long":
            return all(prices[i] >
                       prices[i+1] for i
                       in range(len(prices)-1))
        else:
            return all(prices[i] <
                       prices[i+1] for i
                       in range(len(prices)-1))

    def adjust_SL(self):
        """Adjust SL"""
        newSL_price = (UnawareTrade.preceding_candles[-1].l
                       if self.type == "long" else
                       UnawareTrade.preceding_candles[-1].h)
        self.SL = newSL_price

    def run_trade(self, connect: bool = True) -> None:
        """Method to run this UnawareTrade.

        Arguments:
            connect: If True then it will use the API to fetch candles

        This function will run the trade and will set the outcome attribute
        """
        count = 0
        for d in self.gen_datelist():
            count += 1
            cl = self.clist[d]
            if cl is None:
                if connect is True:
                    cl = self._fetch_candle(d=d)
                if cl is None:
                    continue
            cl_tm = self.clist_tm[d]
            if cl_tm is None:
                if connect is True:
                    cl_tm = self._fetch_candle(d=d)
            if cl_tm is not None:
                UnawareTrade.preceding_candles.append(cl_tm)
            if len(UnawareTrade.preceding_candles) == self.candle_number:
                res = self.check_if_against()
                if res is True:
                    pdb.set_trace()
                    self.adjust_SL()
                UnawareTrade.preceding_candles = []
            if self._check_candle_overlap(cl, self.SL.price):
                t_logger.info("Sorry, SL was hit!")
                self.outcome = "failure"
            elif self._check_candle_overlap(cl, self.TP.price):
                t_logger.info("Great, TP was hit!")
                self.outcome = "success"
            elif count >= trade_params.numperiods:
                t_logger.warning("No outcome could be calculated in the "
                                 "trade_params.numperiods interval")
                self.outcome = "n.a."
            else:
                continue
            self._finalise_trade(connect=connect, cl=cl)
            return
