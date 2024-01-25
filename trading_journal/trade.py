from __future__ import division
from abc import ABC, abstractmethod
import logging
import pdb

from trading_journal.constants import ALLOWED_ATTRBS, VALID_TYPES
from datetime import datetime
from forex.harea import HArea
from forex.pivot import PivotList
from utils import (
    add_pips2price,
    calculate_pips,
    try_parsing_date,
    substract_pips2price
    )
from trading_journal.trade_utils import (
    gen_datelist,
    fetch_candle_api,
    check_candle_overlap,
    init_clist
)
from params import trade_params

t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)

class Trade(ABC):
    """This is an abstrace class represents a Trade.

    Class variables:
        init_clist: boolean that will be true if 
                    clist and clist_tm should be
                    initialised
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

    def _preinit__(self):
        if not hasattr(self, "clist") and self.init_clist is True:
            self.clist = init_clist(timeframe=self.timeframe,
                                    pair=self.pair,
                                    start=self.start)
        if not hasattr(self, "clist_tm") and self.init_clist is True:
            self.clist_tm = init_clist(timeframe=trade_params.clisttm_tf,
                                       pair=self.pair,
                                       start=self.start)

        self.__dict__.update({"start": try_parsing_date(self.__dict__["start"])})
        if hasattr(self, "end"):
            self.__dict__.update({"end": try_parsing_date(self.__dict__["end"])})

    def __init__(self, entry: float, SL: float, TP: float = None, init_clist=False, **kwargs) -> None:
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in ALLOWED_ATTRBS)
        self.init_clist = init_clist
        self._preinit__()
        self._validate_clists()
        self.entry = self.init_harea(entry) if not isinstance(entry, HArea) else entry
        self.SL = self.init_harea(SL) if not isinstance(SL, HArea) else SL
        if kwargs.get("RR") is None and TP is None:
            raise ValueError(
                "Neither the RR not " "the TP is defined. Please provide at least one!"
            )
        if kwargs.get("RR") is not None and TP is None:
            TP = self.calc_TP()
        elif kwargs.get("RR") is None and TP is not None:
            RR = self.calc_RR(TP=TP)
            self.RR = RR
        self.TP = self.init_harea(TP) if not isinstance(TP, HArea) else TP
        self.SLdiff = self.get_SLdiff()


    def init_harea(self, price: float) -> HArea:
        harea_obj = HArea(price=price,
                            instrument=self.pair,
                            pips=trade_params.hr_pips,
                            granularity=self.timeframe)
        return harea_obj


    def _validate_clists(self):
        """Method to check the validity of the clists"""
        if hasattr(self, "clist"):
            if self.clist.instrument != self.pair or self.clist.granularity != self.timeframe:
                raise("Incompatible clist attributes")

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
        for d in gen_datelist(start=self.start, timeframe=self.timeframe):
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
                    cl = fetch_candle_api(d=d, pair=self.pair, timeframe=self.timeframe)
                if cl is None:
                    count -= 1
                    continue
            if check_candle_overlap(cl, self.entry.price):
                t_logger.info("Trade entered")
                self.entered = True
                if connect is True:
                    try:
                        entry_time = self.entry.get_cross_time(
                            candle=cl, granularity=trade_params.granularity
                        )
                        self.entry_time = entry_time.isoformat()
                    except BaseException:
                        self.entry_time = cl.time.isoformat()
                else:
                    self.entry_time = cl.time.isoformat()
                break

    def is_entry_onrsi(self) -> bool:
        """Function to check if self.start is on RSI.

        Arguments:
            trade : Trade object used for the calculation

        Returns:
            True if tObj.start is on RSI (i.e. RSI>=70 or RSI<=30)
        """
        if self.clist[self.start].rsi >= 70 or self.clist[self.start].rsi <= 30:
            return True
        else:
            return False

    def get_lasttime(self, pad: int = 0):
        """Function to calculate the last time price has been above/below
        a certain HArea.

        Arguments:
            trade : Trade object used for the calculation
            pad : Add/substract this number of pips to trade.SR
        """
        new_SR = self.SR
        if pad > 0:
            if self.type == "long":
                new_SR = substract_pips2price(self.clist.instrument, self.SR, pad)
            elif self.type == "short":
                new_SR = add_pips2price(self.clist.instrument, self.SR, pad)
        newcl = self.clist.slice(start=self.clist.candles[0].time, end=self.start)
        return newcl.get_lasttime(new_SR, type=self.type)

    def calc_TP(self) -> float:
        diff = (self.entry.price - self.SL.price) * self.RR
        return round(self.entry.price + diff, 4)

    def calc_RR(self, TP: float) -> float:
        RR = abs(TP - self.entry.price) / abs(self.SL.price - self.entry.price)
        return round(RR, 2)

    def get_trend_i(self) -> datetime:
        """Function to calculate the start of the trend"""
        pvLst = PivotList(self.clist)
        merged_s = pvLst.calc_itrend()

        if self.type == "long":
            candle = merged_s.get_highest()
        elif self.type == "short":
            candle = merged_s.get_lowest()

        return candle.time

    def get_SLdiff(self) -> float:
        """Function to calculate the difference in number of pips between the
        entry and the SL prices.

        Returns:
            number of pips
        """
        diff = abs(self.entry.price - self.SL.price)
        number_pips = float(calculate_pips(self.pair, diff))

        return number_pips

    @abstractmethod
    def run(self, expires: int = 2, connect=True) -> None:
        """Run the trade until conclusion from a start datetime."""
        pass

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append(f"{key}='{self.__dict__[key]}'")
        return ", ".join(sb)

    def __repr__(self):
        return "Trade"
