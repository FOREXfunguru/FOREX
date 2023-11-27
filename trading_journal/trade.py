from __future__ import division
from abc import ABC, abstractmethod
import logging
import pdb

from trading_journal.constants import ALLOWED_ATTRBS, VALID_TYPES
from datetime import datetime
from forex.harea import HArea
from utils import try_parsing_date
from trade_utils import (
    calc_TP,
    calc_RR,
    gen_datelist,
    get_SLdiff,
    fetch_candle,
    finalise_trade,
    init_harea,
    init_clist,
    check_candle_overlap
)
from params import trade_params
from api.oanda.connect import Connect

t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)


class Trade(ABC):
    """This is an abstrace class represents a Trade.

    Class variables:
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
            self.clist = init_clist(self.timeframe)
        if not hasattr(self, "clist_tm"):
            self.clist_tm = init_clist(trade_params.clisttm_tf)
        if self.clist_tm.instrument != self.clist_tm.instrument:
            raise ValueError("Inconsistent instruments between 'clist' and 'clist_tm'")

        self.__dict__.update({"start":
                              try_parsing_date(self.__dict__["start"])})
        if hasattr(self, "end"):
            self.__dict__.update({"end":
                                  try_parsing_date(self.__dict__["end"])})

    def __init__(self,
                 entry: float,
                 SL: float,
                 TP: float = None,
                 **kwargs) -> None:
        self.__dict__.update((k, v) for k, v in kwargs.items()
                             if k in ALLOWED_ATTRBS)
        self.__preinit__()
        self.entry = init_harea(entry) if not isinstance(entry, HArea) else entry
        self.SL = init_harea(SL) if not isinstance(SL, HArea) else SL
        if kwargs.get("RR") is None and TP is None:
            raise ValueError("Neither the RR not "
                             "the TP is defined. Please provide at least one!")
        if kwargs.get("RR") is not None and TP is None:
            TP = calc_TP(self, RR=kwargs.get("RR"))
        elif kwargs.get("RR") is None and TP is not None:
            RR = calc_RR(self, TP=TP)
            self.RR = RR
        self.TP = init_harea(TP) if not isinstance(TP, HArea) else TP
        self.SLdiff = get_SLdiff()

    def initialise(self, expires: int = 2, connect=True) -> None:
        """Progress the trade and check if taken. 
        
        Arguments:
            expires: Number of candles after start datetime to check
                     for entry
            connect: If True then it will use the API to fetch candles
        """
        t_logger.info(f"Initialising trade: {self.pair}:{self.start}")
        count = 0
        self.entered = False
        for d in gen_datelist(self):
            if d.weekday() == 5:
                continue
            count += 1
            if (count > expires or d > datetime.now()) and self.entered is False:
                t_logger.warning("Trade entry expired or is in the future!")
                self.outcome = "n.a."
                self.pips = 0
                return
            cl = self.clist[d]
            if cl is None:
                if connect is True:
                    cl = fetch_candle(d=d)
                if cl is None:
                    count -= 1
                    continue
            if check_candle_overlap(cl, self.entry.price):
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
                break

    def run(self, expires: int = 2, connect=True) -> None:
        """Run the trade until conclusion from a start datetime.

        """
        t_logger.info(f"Run run_trade with id: {self.pair}:{self.start}")

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
                    cl = fetch_candle(d=d)
                if cl is None:
                    continue
            cl_tm = self.clist_tm[d]
            if cl_tm is None:
                if connect is True:
                    cl_tm = fetch_candle(d=d)
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
            trade = finalise_trade(self, connect=connect, cl=cl)
            return trade
