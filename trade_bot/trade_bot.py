import logging
import pickle
import re

from datetime import datetime, timedelta
from typing import List
from api.oanda.connect import Connect
from forex.candle import CandleList, Candle
from forex.harea import HAreaList
from params import gparams, tradebot_params, pivots_params
from forex.pivot import PivotList
from forex.candlelist_utils import calc_SR
from trading_journal.trade import Trade
from trade_bot.trade_bot_utils import (adjust_SL_candles,
                                       adjust_SL_nextSR,
                                       get_trade_type,
                                       prepare_trade)
from trade_bot.trade_bot_utils import adjust_SL_pips
from dataclasses import dataclass
from utils import try_parsing_date, periodToDelta

# create logger
tb_logger = logging.getLogger(__name__)
tb_logger.setLevel(logging.INFO)


@dataclass
class preTrade:
    """Container for a Candle falling on a HArea, which can potentially become
    a trade"""
    sel_ix: int
    SRlst: HAreaList
    candle: Candle
    type: str


class TradeBot(object):
    '''This class represents an automatic Trading bot.

    Class variables:
        start: datetime that this Bot will start operating.
               i.e. 20-03-2017 08:20:00s
        end: datetime that this Bot will end operating.
             i.e. 20-03-2020 08:20:00s
        pair: Currency pair used in the trade. i.e. AUD_USD
        timeframe: Timeframe used for the trade. Possible values are:
                   D,H12,H10,H8,H4,H1
        clist: CandleList object used to represent this trade
    '''
    __slots__ = ["start", "end", "pair", "timeframe", "clist",
                 "delta_period", "delta"]

    def __init__(self, start: datetime, end: datetime, pair: str,
                 timeframe: str, clist: CandleList = None):
        self.start = try_parsing_date(start)
        self.end = try_parsing_date(end)
        self.pair = pair
        self.timeframe = timeframe
        self.clist = clist
        self.delta_period = periodToDelta(tradebot_params.period_range,
                                          self.timeframe)
        if self.timeframe == "D":
            self.delta = timedelta(hours=24)
        else:
            p1 = re.compile('^H')
            m1 = p1.match(self.timeframe)
            if m1:
                nhours = int(self.timeframe.replace('H', ''))
                self.delta = timedelta(hours=nhours)
        if not clist:
            self.init_clist()
        else:
            if clist.candles[-1].time < self.end:
                logging.warning(f"Tradebot end:{self.end} is greater than "
                                f"clist end: {clist.candles[-1].time}")
                self.init_clist()

    def init_clist(self) -> None:
        """Init clist for this TradeBot"""

        conn = Connect(
            instrument=self.pair,
            granularity=self.timeframe)
        if tradebot_params.period_range > 4899:
            tradebot_params.period_range = 4899
        initc_date = self.start-self.delta_period

        clO = conn.query(initc_date.isoformat(), self.end.isoformat())
        self.clist = clO

    def scan(self, discard_sat: bool = True) -> List[preTrade]:
        """This function will scan for candles on S/R areas.
        These candles will be written to a .csv file

        Arguments:
            discard_sat: If True, then the Trade wil not
                         be taken if IC falls on a Saturday
        """
        tb_logger.info("Running...")

        pretrades = []
        startO = self.start
        loop = 0
        while startO <= self.end:
            tb_logger.debug(f"Trade bot - analyzing candle: {startO.isoformat()}")
            # Get now a CandleList from 'initc_date' to 'self.start'
            #  which is the total time interval for this TradeBot
            initc_date = startO-self.delta_period
            if loop == 0 or loop >= tradebot_params.period:
                subclO = self.clist.slice(initc_date, startO)
                sub_pvtlst = PivotList(clist=subclO)
                if pivots_params.plot is True:
                    dt_str = startO.strftime("%d_%m_%Y_%H_%M")
                    outfile_png = (f"{gparams.outdir}/{self.pair}."
                                   f"{self.timeframe}.{dt_str}.halist.png")
                    # print SR report to file
                    outfile_txt = (f"{gparams.outdir}/{self.pair}."
                                   f"{self.timeframe}.{dt_str}.halist.txt")
                    SRlst = calc_SR(sub_pvtlst, outfile=outfile_png)
                    res = SRlst.print()
                    f = open(outfile_txt, 'w')
                    f.write(res+"\n")
                    f.close()
                else:
                    SRlst = calc_SR(sub_pvtlst)
                    res = SRlst.print()
                tb_logger.info("Identified HAreaList for"
                               f"time:{startO.isoformat()}")
                tb_logger.info(f"{res}")
                loop = 0

            # Fetch candle for current datetime. this is the current candle
            # that is being checked
            c_candle = self.clist[startO]
            if c_candle is None:
                startO = startO+self.delta
                loop += 1
                continue

            # c_candle.time is not equal to startO
            # when startO is non-working day, for example
            delta1hr = timedelta(hours=1)
            if (c_candle.time != startO) and \
                    (abs(c_candle.time-startO) > delta1hr):
                loop += 1
                tb_logger.info(f"Analysed dt {startO} is not the same than "
                               f"APIs returned dt {c_candle.time}."
                               " Skipping...")
                startO = startO + self.delta
                continue

            # check if there is any HArea overlapping with c_candle
            HAreaSel, sel_ix = SRlst.onArea(candle=c_candle)
            if HAreaSel is not None:
                # guess the if trade is 'long' or 'short'
                newCl = self.clist.slice(start=initc_date, end=c_candle.time)
                type = get_trade_type(c_candle.time, newCl)

                prepare = False
                if c_candle.indecision_c(ic_perc=gparams.ic_perc) is True and \
                        len(SRlst.halist) >= 3 and \
                        c_candle.height(pair=self.pair) \
                        < tradebot_params.max_height:
                    prepare = True
                elif type == 'short' and c_candle.colour == 'red' and \
                        len(SRlst.halist) >= 3 and \
                        c_candle.height(pair=self.pair) < \
                        tradebot_params.max_height:
                    prepare = True
                elif type == 'long' and c_candle.colour == 'green' and \
                        len(SRlst.halist) >= 3 and \
                        c_candle.height(pair=self.pair) < \
                        tradebot_params.max_height:
                    prepare = True

                # discard if IC falls on a Saturday
                if c_candle.time.weekday() == 5 and discard_sat is True:
                    tb_logger.info(f"Possible trade at {c_candle.time} "
                                   f"falls on Sat. Skipping...")
                    prepare = False

                if prepare is True:
                    pretrades.append(preTrade(sel_ix=sel_ix,
                                              SRlst=SRlst,
                                              candle=c_candle,
                                              type=type))

            startO = startO+self.delta
            loop += 1
        tb_logger.info("Run done")
        return pretrades

    def prepare_trades(self, pretrades: str) -> List[Trade]:
        """This function unpickles the preTrade objects
        identified by self.scan() and will create a list of Trade objects

        Arguments:
            pretrades: Pickled file with a list of preTrade objects
        """
        TP = None
        tlist = []
        with open(pretrades, "rb") as f:
            pret_lst = pickle.load(f)
            for pret in pret_lst:
                initc_date = pret.candle.time-self.delta_period
                newCl = self.clist.slice(start=initc_date,
                                         end=pret.candle.time)
                if tradebot_params.adj_SL == "candles":
                    SL = adjust_SL_candles(pret.type, newCl)
                elif tradebot_params.adj_SL == "pips":
                    SL = adjust_SL_pips(pret.candle,
                                        pret.type,
                                        pair=self.pair,
                                        no_pips=tradebot_params.adj_SL_pips)
                else:
                    SL, TP = adjust_SL_nextSR(pret.SRlst,
                                              pret.sel_ix,
                                              pret.type)
                    if not SL:
                        SL = adjust_SL_pips(pret.candle,
                                            pret.type,
                                            pair=self.pair,
                                            no_pips=tradebot_params.adj_SL_pips)
                t = prepare_trade(
                        tb_obj=self,
                        start=pret.candle.time+self.delta,
                        type=pret.type,
                        ic=pret.candle,
                        SL=SL,
                        TP=TP,
                        harea_sel=pret.SRlst.halist[pret.sel_ix],
                        add_pips=tradebot_params.add_pips)
                t.tot_SR = len(pret.SRlst.halist)
                t.rank_selSR = pret.sel_ix
                tlist.append(t)
        return tlist
