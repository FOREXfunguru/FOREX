import logging
from datetime import datetime

from trading_journal.trade import Trade
from forex.harea import HArea
from forex.candle import Candle
from utils import periodToDelta, calculate_profit
from trading_journal.trade_utils import (
    gen_datelist,
    fetch_candle_api,
    check_candle_overlap,
    process_start,
    adjust_SL,
    check_timeframes_fractions,
)
from params import trade_params

t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)

class OpenTrade(Trade):
    """Class to represent an open Trade"""
    def __init__(self,
                 candle_number: int = 3,
                 connect: bool = True,
                 **kwargs):
        """Constructor

        Arguments:
            candle_number: number of candles against the trade to consider
            connect: If True then it will use the API to fetch candles
        """
        self.candle_number = candle_number
        self.connect = connect
        self.preceding_candles = list()
        super().__init__(**kwargs)
    
    def append_trademanagement_candles(self,
                                       aligned_d: datetime,
                                       fraction: float,
                                       connect: bool):
        """Append the trademanagement candles to self.preceding_candles"""
        delta = periodToDelta(ncandles=1,
                              timeframe=trade_params.clisttm_tf)
        if fraction < 1:
            fraction = 1 
        for ix in range(int(fraction)):
            new_datetime = aligned_d + delta*ix
            cl_tm = self.clist_tm[new_datetime]
            if cl_tm is None:
                if connect is True:
                    cl_tm = fetch_candle_api(d=new_datetime,
                                             pair=self.pair,
                                             timeframe=trade_params.clisttm_tf)
            
            if cl_tm is not None:
                if cl_tm not in self.preceding_candles:
                    self.preceding_candles.append(cl_tm)
        
        # slice to self.candle_number if more than this number
        if len(self.preceding_candles) > self.candle_number:
            self.preceding_candles = self.preceding_candles[(self.candle_number)*-1:]

    def check_if_against(self):
        """Function to check if middle_point values are
        agaisnt the trade
        """
        prices = [x.middle_point() for x in self.preceding_candles]
        if self.type == "long":
            return all(prices[i] > prices[i + 1] for i in range(len(prices) - 1))
        else:
            return all(prices[i] < prices[i + 1] for i in range(len(prices) - 1))

    def end_trade(self, connect: bool,
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
    
    def finalise_trade(self, connect: bool, cl: Candle) -> None:
        """Finalise  trade by setting the outcome and calculating profit"""
        if self.outcome == "success":
            price1 = self.TP.price
            self.end_trade(
                    connect=connect,
                    cl=cl,
                    harea=self.TP)
        if self.outcome == "failure":
            price1 = self.SL.price
            self.end_trade(
                    connect=connect,
                    cl=cl,
                    harea=self.SL)
        if self.outcome == "n.a.":
            price1 = cl.c
            self.end = "n.a."
            self.exit = price1
        if self.outcome == "future":
            self.end = "n.a."
            self.pips = "n.a."
            self.exit = "n.a."
        if self.outcome != "future":
            self.pips = calculate_profit(prices=(price1,
                                                self.entry.price),
                                                type=self.type,
                                                pair=self.pair)


class UnawareTrade(OpenTrade):
    """Class to represent an open Trade of the 'area_unaware' type"""

    def __init__(self, **kwargs):
        """Constructor"""
        super().__init__(**kwargs)

    def run(self) -> None:
        """Method to run this UnawareTrade.

        This function will run the trade and will set the outcome attribute
        """
        fraction = check_timeframes_fractions(timeframe1=self.timeframe,
                                              timeframe2=trade_params.clisttm_tf)

        current_date = datetime.now().date()
        count = 0
        completed = False
        for d in gen_datelist(start=self.start, timeframe=self.timeframe):
            print(d)
            if d.date() == current_date:
                logging.warning("Skipping, as unable to end the trade")
                self.outcome = "future"
                break
            if d > self.clist.candles[-1].time and connect is False:
                raise Exception("No candle is available in 'clist' and connect is False. Unable to follow")
            if completed:
                break
            count += 1
            cl = self.clist[d]
            if cl is None:
                if connect is True:
                    cl = fetch_candle_api(d=d,
                                          pair=self.pair,
                                          timeframe=self.timeframe)
                if cl is None:
                    count -= 1
                    continue
            # align 'd' object to 'trade_params.clisttm_tf' timeframe
            aligned_d = process_start(dt=d, timeframe=trade_params.clisttm_tf)
            self.append_trademanagement_candles(aligned_d, fraction, connect)

            if len(self.preceding_candles) == self.candle_number:
                res = self.check_if_against()
                if res is True:
                    new_SL = adjust_SL(pair=self.pair, 
                                       type=self.type,
                                       list_candles=self.preceding_candles)
                    self.SL.price = new_SL
                self.preceding_candles = list()
            if check_candle_overlap(cl, self.SL.price):
                t_logger.info("Sorry, SL was hit!")
                completed = True
                self.outcome = "failure"
            elif check_candle_overlap(cl, self.TP.price):
                t_logger.info("Great, TP was hit!")
                completed = True
                self.outcome = "success"
            elif count >= trade_params.numperiods:
                completed = True
                t_logger.warning(
                    "No outcome could be calculated in the "
                    "trade_params.numperiods interval"
                )
                self.outcome = "n.a."
            else:
                continue
        self.finalise_trade(connect=connect, cl=cl)
         
