import pdb

from trading_journal.trade import Trade
from forex.candle import CandleList


class UnawareTrade(Trade):
    """Class to represent an open Trade of the 'area_unaware' type"""

    preceding_candles = []

    def __init__(self,
                 candle_number: int = 3,
                 clist_tm: CandleList = None,
                 **kwargs):
        """Constructor

        Arguments:
            candle_number: number of candles against the trade to consider
            clist_tm: CandleList used for trade management
        """
        self.candle_number = candle_number
        super().__init__(**kwargs)
        self.clist_tm = clist_tm

    @property
    def clist_tm(self):
        return self._clist_tm

    @clist_tm.setter
    def clist_tm(self, clist: CandleList):
        if self.start > clist.candles[-1].time:
            raise ValueError("Incorrect 'clist_tm'. Trade start "
                             "does not match the end of 'clist_end'")
        if clist.instrument != self.clist.instrument:
            raise ValueError("Instruments self.clist_tm/self.clist differ!")

        self._clist_tm = clist

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

    def run(self, connect: bool = True):
        """Method to run this UnawareTrade.

        Arguments:
            connect: If True then it will use the API to fetch candles
        """
        for d in self.gen_datelist():
            cl = self.clist[d]
            if cl is None:
                if connect is True:
                    cl = self._fetch_candle(d=d)
                if cl is None:
                    continue
            cl_tm = self.clist_tm[d]
            if cl_tm is not None:
                UnawareTrade.preceding_candles.append(cl_tm)
            if len(UnawareTrade.preceding_candles) == 3:
                res = self.check_if_against()
                if res is True:
                    newSL_price = (UnawareTrade.preceding_candles[-1].l
                                   if self.type == "long" else
                                   UnawareTrade.preceding_candles[-1].h)

                    self.SL = newSL_price
                UnawareTrade.preceding_candles = []