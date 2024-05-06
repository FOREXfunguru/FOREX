import logging

from datetime import datetime

from trading_journal.trade import Trade
from api.oanda.connect import Connect
from forex.harea import HArea
from forex.candle import Candle
from utils import (
    periodToDelta,
    calculate_profit,
    add_pips2price,
    substract_pips2price)
from trading_journal.trade_utils import (
    gen_datelist,
    check_candle_overlap,
    process_start,
    adjust_SL,
    check_timeframes_fractions,
)
from params import trade_management_params

t_logger = logging.getLogger(__name__)
t_logger.setLevel(logging.INFO)


class OpenTrade(Trade):
    """An open Trade (i.e. entered)"""

    def __init__(self, candle_number: int = 3, connect: bool = True, **kwargs):
        """Constructor.

        Arguments:
            candle_number: number of candles against the trade to consider
            connect: If True then it will use the API to fetch candles
            completed: Is this Trade completed?
            preceding_candles: Number of candles to check if CandleList
                               goes against the trade
        """
        self.candle_number = candle_number
        self.connect = connect
        self.completed = False  # is this OpenTrade completed
        self.preceding_candles = list()
        super().__init__(**kwargs)

    def append_trademanagement_candles(self, aligned_d: datetime, fraction: float):
        """Append the trademanagement candles to self.preceding_candles"""
        delta = periodToDelta(ncandles=1, timeframe=trade_management_params.clisttm_tf)
        if fraction < 1:
            fraction = 1
        for ix in range(int(fraction)):
            new_datetime = aligned_d + delta * ix
            cl_tm = self.clist_tm[new_datetime]
            if cl_tm is None:
                if self.connect is True:
                    conn = Connect(
                        instrument=self.pair, granularity=trade_management_params.clisttm_tf
                    )
                    cl_tm = conn.fetch_candle(d=new_datetime)
            if cl_tm is not None:
                if cl_tm not in self.preceding_candles:
                    self.preceding_candles.append(cl_tm)

        # slice to self.candle_number if more than this number
        if len(self.preceding_candles) > self.candle_number:
            self.preceding_candles = self.preceding_candles[(self.candle_number) * -1:]

    def process_trademanagement(self, d: datetime, fraction: float):
        """Process trademanagement candles and ajust SL if required"""
        # align 'd' object to 'trade_management_params.clisttm_tf' timeframe
        aligned_d = process_start(dt=d, timeframe=trade_management_params.clisttm_tf)
        self.append_trademanagement_candles(aligned_d, fraction)

        if len(self.preceding_candles) == self.candle_number:
            res = self.check_if_against()
            if res is True:
                new_SL = adjust_SL(
                    pair=self.pair, type=self.type, list_candles=self.preceding_candles
                )
                self.SL.price = new_SL
            if trade_management_params.preceding_clist_strat == "wipe":
                self.preceding_candles = list()
            elif trade_management_params.preceding_clist_strat == "queue":
                self.preceding_candles = self.preceding_candles[1:]
            else:
                raise NotImplementedError(
                    "Invalid trade_management_params.preceding_clist_strat: "
                    f"{trade_management_params.preceding_clist_strat}"
                )

    def check_if_against(self):
        """Function to check if middle_point values are
        agaisnt the trade
        """
        prices = [x.middle_point() for x in self.preceding_candles]
        if self.type == "long":
            return all(prices[i] > prices[i + 1] for i in range(len(prices) - 1))
        else:
            return all(prices[i] < prices[i + 1] for i in range(len(prices) - 1))

    def calculate_overlap(self, cl: Candle) -> None:
        """Check if 'cl' overlaps either self.SL or self.TP.

        It also sets the outcome
        """
        if check_candle_overlap(cl, self.SL.price):
            t_logger.info("Sorry, SL was hit!")
            self.completed = True
            self.outcome = "failure"
        elif check_candle_overlap(cl, self.TP.price):
            t_logger.info("Great, TP was hit!")
            self.completed = True
            self.outcome = "success"

    def end_trade(self, cl: Candle, harea: HArea) -> None:
        """End trade"""
        end = None
        if self.connect is True:
            end = harea.get_cross_time(candle=cl,
                                       granularity=trade_management_params.granularity)
        else:
            end = cl.time
        self.end = end
        self.exit = harea.price

    def finalise_trade(self, cl: Candle) -> None:
        """Finalise  trade by setting the outcome and calculating profit"""
        if self.outcome == "success":
            price1 = self.TP.price
            self.end_trade(cl=cl, harea=self.TP)
        if self.outcome == "failure":
            price1 = self.SL.price
            self.end_trade(cl=cl, harea=self.SL)
        if self.outcome == "n.a.":
            price1 = cl.c
            self.end = "n.a."
            self.exit = price1
        if self.outcome == "future":
            self.end = "n.a."
            self.pips = "n.a."
            self.exit = "n.a."
        if self.outcome != "future":
            self.pips = calculate_profit(
                prices=(price1, self.entry.price), type=self.type, pair=self.pair
            )

    def fetch_candle(self, d: datetime) -> Candle:
        """Fetch a Candle object given a datetime"""
        cl = None
        cl = self.clist[d]
        if cl is None:
            if self.connect is True:
                conn = Connect(instrument=self.pair,
                               granularity=self.timeframe)
                cl = conn.fetch_candle(d=d)
        return cl

    def isin_profit(self, price: float) -> bool:
        """Is price in profit?.

        Argument:
            price: price to check
        """
        if self.type == "long":
            if price >= self.entry.price:
                return True
        if self.type == "short":
            if price <= self.entry.price:
                return True
        return False


class UnawareTrade(OpenTrade):
    """Represent a trade that ignores whether the price is in profit or loss.

    Characterizes for not being conditioned by the price being in loss or profit 
    (hence the name 'unaware') to begin to add candles to 'start.preceding_candles'."
    """

    def __init__(self, **kwargs):
        """Constructor"""
        super().__init__(**kwargs)

    def run(self) -> None:
        """Method to run this UnawareTrade.

        This function will run the trade and will set the outcome attribute
        """
        fraction = check_timeframes_fractions(
            timeframe1=self.timeframe,
            timeframe2=trade_management_params.clisttm_tf
        )

        current_date = datetime.now().date()
        count = 0
        for d in gen_datelist(start=self.start, timeframe=self.timeframe):
            if d.date() == current_date:
                logging.warning("Skipping, as unable to end the trade")
                self.outcome = "future"
                break
            if d > self.clist.candles[-1].time and self.connect is False:
                raise Exception(
                    "No candle is available in 'clist' and connect is False. Unable to follow"
                )
            if self.completed:
                break
            count += 1
            cl = self.fetch_candle(d)
            if cl is None:
                count -= 1
                continue
            self.process_trademanagement(d=d, fraction=fraction)
            self.calculate_overlap(cl=cl)
            if count >= trade_management_params.numperiods:
                self.completed = True
                t_logger.warning(
                    "No outcome could be calculated in the "
                    "trade_params.numperiods interval"
                )
                self.outcome = "n.a."
        self.finalise_trade(cl=cl)


class AwareTrade(OpenTrade):
    """Represent a trade that is aware of the price being in profit or loss.

    Characterizes for adding candles to 'start.preceding_candles' only if price is in profit
    """

    def __init__(self, **kwargs):
        """Constructor"""
        super().__init__(**kwargs)

    def run(self) -> None:
        """Method to run this AwareTrade.

        This function will run the trade and will set the outcome attribute
        """
        fraction = check_timeframes_fractions(
            timeframe1=self.timeframe,
            timeframe2=trade_management_params.clisttm_tf
        )

        current_date = datetime.now().date()
        count = 0
        for d in gen_datelist(start=self.start, timeframe=self.timeframe):
            if d.date() == current_date:
                logging.warning("Skipping, as unable to end the trade")
                self.outcome = "future"
                break
            if d > self.clist.candles[-1].time and self.connect is False:
                raise Exception(
                    "No candle is available in 'clist' and connect is False. Unable to follow"
                )
            if self.completed:
                break
            count += 1
            cl = self.fetch_candle(d)
            if cl is None:
                count -= 1
                continue
            if self.isin_profit(price=cl.c):
                self.process_trademanagement(d=d, fraction=fraction)
            else:
                self.preceding_candles = list()

            self.calculate_overlap(cl=cl)
            if count >= trade_management_params.numperiods:
                self.completed = True
                t_logger.warning(
                    "No outcome could be calculated in the "
                    "trade_params.numperiods interval"
                )
                self.outcome = "n.a."
        self.finalise_trade(cl=cl)


class BreakEvenTrade(OpenTrade):
    """Represent a trade that adjusts SL to breakeven when in profit.

    When 'self.SL' is adjusted to breakeven, then candles will start
    being added to 'self.preceding_candles'
    """

    def __init__(self, number_of_pips=20, **kwargs):
        """Constructor
        Arguments:
            number_of_pips = Number of pips in profit to move to breakeven.
                             This parameter will also control the SL new price,
                             which will be (self.entry+number_of_pips) minus 10
                             pips
        """
        self.number_of_pips = number_of_pips
        super().__init__(**kwargs)

    def run(self) -> None:
        """Method to run this BreakEvenTrade.

        This function will run the trade and will set the outcome attribute
        """
        fraction = check_timeframes_fractions(
            timeframe1=self.timeframe,
            timeframe2=trade_management_params.clisttm_tf
        )

        current_date = datetime.now().date()
        count = 0
        for d in gen_datelist(start=self.start, timeframe=self.timeframe):
            if d.date() == current_date:
                logging.warning("Skipping, as unable to end the trade")
                self.outcome = "future"
                break
            if d > self.clist.candles[-1].time and self.connect is False:
                raise Exception(
                    "No candle is available in 'clist' and connect is False."
                    "Unable to follow"
                )
            count += 1
            cl = self.fetch_candle(d)
            if cl is None:
                count -= 1
                continue

            self.calculate_overlap(cl=cl)
            if self.completed:
                break
            pips_distance = calculate_profit(
                prices=(cl.c, self.entry.price), type=self.type, pair=self.pair
            )
            if pips_distance > self.number_of_pips:
                # This controls the gain achieved when moving the SL price
                pips_of_gain = self.number_of_pips - 10
                if self.type == "long":
                    new_price = add_pips2price(
                        pair=self.pair, price=self.entry.price,
                        pips=pips_of_gain
                    )
                elif self.type == "short":
                    new_price = substract_pips2price(
                        pair=self.pair, price=self.entry.price,
                        pips=pips_of_gain
                    )
                self.SL.price = new_price

            self.process_trademanagement(d=d, fraction=fraction)

            if count >= trade_management_params.numperiods:
                self.completed = True
                t_logger.warning(
                    "No outcome could be calculated in the "
                    "trade_management_params.numperiods interval"
                )
                self.outcome = "n.a."
        self.finalise_trade(cl=cl)
