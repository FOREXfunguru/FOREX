from __future__ import division

import logging

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
ALLOWED_ATTRBS = ['entered', 'start', 'end', 'pair', 'timeframe',
                  'outcome', 'entry', 'exit', 'entry_time', 'type',
                  'SL', 'TP', 'SR', 'RR', 'pips', 'clist', 'strat',
                  'tot_SR', 'rank_selSR']


class Trade(object):
    """This is the parent class represents a single row from the TradeJournal
       class.

    Class variables:
        entered: False if trade not taken (price did not cross self.entry). 
                 True otherwise
        start: Time/date when the trade was taken. i.e. 20-03-2017 08:20:00s
        pair: Currency pair used in the trade. i.e. AUD_USD
        timeframe: Timeframe used for the trade. Possible values are: D,H12,
                                                 H10,H8,H4
        outcome: Outcome of the trade. Possible values are: success, failure,
                                                            breakeven
        entry: entry price
        exit: exit price
        entry_time: Datetime for price reaching the entry price
        type: What is the type of the trade (long,short)
        SL:  float, Stop/Loss price
        TP:  float, Take profit price. If not defined then it will calculated
             by using the RR
        SR:  float, Support/Resistance area
        RR:  float, Risk Ratio
        pips:  Number of pips of profit/loss. This number will be negative if
               outcome was failure
        clist: CandleList object used to represent this trade"""
    def __init__(self, init_clist: bool = False, **kwargs) -> None:
        self.__dict__.update((k, v) for k, v in kwargs.items()
                             if k in ALLOWED_ATTRBS)
        if init_clist and not hasattr(self, 'clist'):
            self.init_clist()
        self.__dict__.update({'start':
                              try_parsing_date(self.__dict__['start'])})
        if hasattr(self, 'end') and isinstance(self.end, datetime):
            self.__dict__.update({'end':
                                  try_parsing_date(self.__dict__['end'])})
        self._validate_params()
        self.SLdiff = self.get_SLdiff()
        self.entered = False

    def _validate_params(self) -> None:
        if (getattr(self, 'TP', None) is None) and \
                (getattr(self, 'RR', None) is None):
            raise Exception("Neither the RR not "
                            "the TP is defined. Please provide RR")
        elif (getattr(self, 'RR', None) is not None) and \
                (getattr(self, 'TP', None) is None):
            diff = (self.entry - self.SL) * self.RR
            self.TP = round(self.entry + diff, 4)
        elif (getattr(self, 'RR', None) is None) and \
                (getattr(self, 'TP', None) is not None):
            RR = abs(self.TP-self.entry)/abs(self.SL-self.entry)
            self.RR = round(RR, 2)

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

    def _calc_HAreas(self) -> tuple[HArea, HArea, HArea]:
        """Private method that returns an entry, SL and TP HArea objects"""

        harealst = []
        for attrb in ["entry", "SL", "TP"]:
            price = getattr(self, attrb)
            harea_obj = HArea(price=price,
                              instrument=self.pair,
                              pips=trade_params.hr_pips,
                              granularity=self.timeframe)
            harealst.append(harea_obj)

        return (harealst[0], harealst[1], harealst[2])

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

    def run_trade(self, expires: int = 2, connect=True) -> None:
        """Run the trade until conclusion from a start date.

        Arguments:
            expires : Number of candles after start datetime to check
                      for entry
        """
        t_logger.info(f"Run run_trade with id: {self.pair}:{self.start}")

        (entry, SL, TP) = self._calc_HAreas()
        period = self._calc_period()

        # generate a range of dates starting at self.start and ending
        # trade_params.interval later in order to assess the outcome
        # of trade and also the entry time
        date_list = [self.start + timedelta(hours=x*period)
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
                if self._check_candle_overlap(cl, self.entry):
                    t_logger.info("Trade entered")
                    self.entered = True
                    if connect is True:
                        try:
                            entry_time = (entry.get_cross_time(candle=cl,
                                          granularity=trade_params.granularity))
                            self.entry_time = entry_time.isoformat()
                        except BaseException:
                            self.entry_time = cl.time.isoformat()
                    else:
                        self.entry_time = cl.time.isoformat()
            if self.entered is True:
                # check if failure
                if self._check_candle_overlap(cl, SL.price):
                    t_logger.info("Sorry, SL was hit!")
                    self.outcome = "failure"
                    self.pips = calculate_profit(prices=(SL.price, self.entry),
                                                 type=self.type,
                                                 pair=self.pair)
                    self._end_trade(connect=connect, cl=cl, harea=SL)
                    return
                # check if success
                if self._check_candle_overlap(cl, TP.price):
                    t_logger.info("Great, TP was hit!")
                    self.outcome = "success"
                    self.pips = calculate_profit(prices=(TP.price, self.entry),
                                                 type=self.type,
                                                 pair=self.pair)
                    self._end_trade(connect=connect, cl=cl, harea=TP)
                    return
                if count >= trade_params.numperiods:
                    t_logger.warning("No outcome could be calculated in the "
                                     "trade_params.numperiods interval")
                    self.pips = calculate_profit(prices=(cl.c, self.entry),
                                                 type=self.type,
                                                 pair=self.pair)
                    self.outcome = "n.a."
                    return
        t_logger.info("Done run_trade")

    def get_SLdiff(self) -> float:
        """Function to calculate the difference in number of pips between the
        entry and the SL prices.

        Returns:
            number of pips
        """
        diff = abs(self.entry - self.SL)
        number_pips = float(calculate_pips(self.pair, diff))

        return number_pips

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key,
                                               value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
