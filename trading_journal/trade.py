from __future__ import division

import logging

from datetime import datetime, timedelta
from forex.pivot import PivotList
from forex.harea import HArea
from utils import calculate_pips, add_pips2price, try_parsing_date, \
    substract_pips2price, periodToDelta
from params import trade_params
from api.oanda.connect import Connect

# create logger
t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)


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
        allowed_keys = ['entered', 'start', 'end', 'pair', 'timeframe',
                        'outcome', 'entry', 'exit', 'entry_time', 'type',
                        'SL', 'TP', 'SR', 'RR', 'pips', 'clist', 'strat',
                        'tot_SR', 'rank_selSR']
        self.__dict__.update((k, v) for k, v in kwargs.items()
                             if k in allowed_keys)
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

    def _validate_params(self):
        if not hasattr(self, 'TP') and not hasattr(self, 'RR'):
            raise Exception("Neither the RR not "
                            "the TP is defined. Please provide RR")
        elif hasattr(self, 'RR') and not self.TP:
            diff = (self.entry - self.SL) * self.RR
            self.TP = round(self.entry + diff, 4)

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

    def _adjust_tp(self):
        """Adjust TP when trade_params.strat==exit early"""
        tp_pips = float(calculate_pips(self.pair, self.TP))
        entry_pips = float(calculate_pips(self.pair, self.entry))
        diff = abs(tp_pips-entry_pips)
        tp_pips = trade_params.reduce_perc*diff/100
        if self.type == 'long':
            new_tp = add_pips2price(self.pair, self.entry, tp_pips)
        else:
            new_tp = substract_pips2price(self.pair, self.entry, tp_pips)
        return new_tp

    def run_trade(self, expires: int = 2, connect=True) -> None:
        """Run the trade until conclusion from a start date.

        Arguments:
            expires : Number of candles after start datetime to check
                      for entry
        """
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

        # generate a range of dates starting at self.start and ending
        # trade_params.numperiods later in order to assess the outcome
        # of trade and also the entry time
        # date_list will contain a list with datetimes that will be used for
        # running self
        date_list = [self.start + timedelta(hours=x*period)
                     for x in range(0, trade_params.interval)]
        cutoff_dt = self.clist.candles[-1].time
        date_list = [dt for dt in date_list if dt <= cutoff_dt]
        count = 0
        self.entered = False
        for d in date_list:
            if d.weekday() == 5:
                continue
            count += 1
            if expires is not None:
                if count > expires and self.entered is False:
                    t_logger.warning("Trade entry expired!")
                    self.outcome = 'n.a.'
                    break
            dtnow = datetime.now()
            if d > dtnow:
                self.outcome = 'n.a.'
                t_logger.info("Run trade in the future. Skipping...")
                break
            cl = self.clist[d]
            if cl is None and connect is True:
                try:
                    conn = Connect(
                        instrument=self.pair,
                        granularity=self.timeframe)
                    clO = conn.query(start=d.isoformat(), end=d.isoformat())
                    if len(clO.candles) == 1:
                        cl = clO.candles[0]
                    elif len(clO.candles) > 1:
                        raise Exception("No valid number of candles in "
                                        "CandleList")
                    else:
                        # market closed
                        count -= 1
                        continue
                except BaseException:
                    count -= 1
                    continue
            elif cl is None and connect is False:
                count -= 1
                continue
            if self.entered is False:
                if cl.l <= entry.price <= cl.h:
                    t_logger.info("Trade entered")
                    self.entered = True
                    if connect is True:
                        try:
                            entry_time = entry.get_cross_time(candle=cl,
                                                              granularity=trade_params.granularity)
                            self.entry_time = entry_time.isoformat()
                        except BaseException:
                            self.entry_time = cl.time.isoformat()
                    else:
                        self.entry_time = cl.time.isoformat()
            if self.entered is True:
                if trade_params.strat == 'exit_early' and \
                    count >= trade_params.no_candles and \
                        not hasattr(self, 'reduced_TP'):
                    new_tp = self._adjust_tp()
                    self.TP = new_tp
                    TP.price = new_tp
                    self.reduced_TP = True
                # check if failure
                if cl.l <= SL.price <= cl.h:
                    t_logger.info("Sorry, SL was hit!")
                    self.exit = SL.price
                    self.outcome = 'failure'
                    self.pips = float(calculate_pips(self.pair,
                                                     abs(self.SL-self.entry)))*-1
                    if connect is True:
                        try:
                            self.end = SL.get_cross_time(candle=cl,
                                                         granularity=trade_params.granularity)
                        except BaseException:
                            self.end = cl.time
                    else:
                        self.end = cl.time
                    break
                # check if success
                if cl.l <= TP.price <= cl.h:
                    t_logger.info("Great, TP was hit!")
                    # if hasattr(self, 'reduced_TP'):
                    #    self.outcome = 'exit_early'
                    self.outcome = 'success'
                    self.exit = TP.price
                    self.pips = float(calculate_pips(self.pair,
                                                     abs(self.TP - self.entry)))
                    if connect is True:
                        try:
                            self.end = TP.get_cross_time(candle=cl,
                                                         granularity=trade_params.granularity)
                        except BaseException:
                            self.end = cl.time
                    else:
                        self.end = cl.time
                    break
                if count >= trade_params.numperiods:
                    t_logger.warning("No outcome could be calculated in the "
                                     "trade_params.numperiods interval")
                    self.outcome = "n.a."
                    break
        if self.outcome != 'failure' and self.outcome != 'success' \
                and self.outcome != 'exit_early' and self.entered:
            self.outcome = "n.a."
            # pips are calculated using the Candle close price
            if (cl.c - self.entry) < 0:
                sign = -1 if self.type == 'long' else 1
            else:
                sign = 1 if self.type == 'long' else -1
            self.pips = float(calculate_pips(self.pair,
                                             abs(cl.c - self.entry))) * sign
            self.end = cl.time
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
