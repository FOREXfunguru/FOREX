import pdb

from trading_journal.trade import Trade
from forex.candle import CandleList


class UnawareTrade(Trade):
    """Class to represent an open Trade of the 'area_unaware' type"""

    middle_point = []  # middle point of candles record

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
        pdb.set_trace()
        if self.start > clist.candles[-1].time:
            raise ValueError("Incorrect 'clist_tm'. Trade start "
                             "does not match the end of 'clist_end'")
        self._clist_tm = clist

    def check_if_against(self):
        """Function to check if middle_point values are
        agaisnt the trade
        """
        pass

    def run(self, connect: bool = True):
        """Method to run this UnawareTrade.

        Arguments:
            connect: If True then it will use the API to fetch candles
        """
        count = 1
        for d in self.gen_datelist():
            pdb.set_trace()
            cl = self.clist[d]
            if cl is None:
                if connect is True:
                    cl = self._fetch_candle(d=d)
                if cl is None:
                    continue
            cl_tm = self.clist_tm[d]
            if cl_tm is not None:
                pdb.set_trace()
                UnawareTrade.middle_point.append(cl.middle_point())
            if count % self.candle_number == 0:
                self.check_if_against()
            count += 1
         
            print(cl)
