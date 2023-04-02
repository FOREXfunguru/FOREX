import logging
import pdb
import datetime

from datetime import datetime

from api.oanda.connect import Connect
from forex.candle import CandleList
from params import gparams, tradebot_params
from utils import *
from forex.pivot import PivotList
from forex.candlelist_utils import *
from trading_journal.trade_utils import *

# create logger
tb_logger = logging.getLogger(__name__)
tb_logger.setLevel(logging.DEBUG)

class TradeBot(object):
    '''This class represents an automatic Trading bot.

    Class variables:
        start: datetime that this Bot will start operating. i.e. 20-03-2017 08:20:00s
        end: datetime that this Bot will end operating. i.e. 20-03-2020 08:20:00s
        pair: Currency pair used in the trade. i.e. AUD_USD
        timeframe: Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4,H1
        clist: CandleList object used to represent this trade
    '''
    def __init__(self, start:datetime, end:datetime, pair:str, timeframe:str, clist: CandleList=None):
        self.start = try_parsing_date(start)
        self.end = try_parsing_date(end)
        self.pair = pair
        self.timeframe = timeframe
        self.clist = clist
        if not clist or clist.candles[-1].time<self.end:
            self.init_clist()
    
    def init_clist(self)->None:
        '''Init clist for this TradeBot'''

        conn = Connect(
            instrument=self.pair,
            granularity=self.timeframe)
        if tradebot_params.period_range>4899:
            tradebot_params.period_range=4899
        delta_period = periodToDelta(tradebot_params.period_range,
                                    self.timeframe)
        initc_date = self.start-delta_period

        clO = conn.query(initc_date.isoformat(), self.end.isoformat())
        self.clist = clO
        
    def run(self, discard_sat: bool=True):
        '''This function will run the Bot from start to end
        one candle at a time.

        Arguments:
            discard_sat: If True, then the Trade wil not
                         be taken if IC falls on a Saturday

        Returns:
            TradeList object with possible Trades. None if no trades
            were found
        '''
        tb_logger.info("Running...")
        delta = nhours = None
        if self.timeframe == "D":
            nhours = 24
            delta = timedelta(hours=24)
        else:
            p1 = re.compile('^H')
            m1 = p1.match(self.timeframe)
            if m1:
                nhours = int(self.timeframe.replace('H', ''))
                delta = timedelta(hours=int(nhours))

        startO = self.start
        loop = 0
        SRlst, TP = None, None
        tlist = []
        while startO <= self.end:
            tb_logger.info("Trade bot - analyzing candle: {0}".format(startO.isoformat()))
            # Get now a CandleList from 'initc_date' to 'self.start' which is the
            # total time interval for this TradeBot
            delta_period = periodToDelta(tradebot_params.period_range,
                                         self.timeframe)
            initc_date = startO-delta_period
            subclO = self.clist.slice(initc_date, startO)
            sub_pvtlst = PivotList(clist=subclO)
            dt_str = startO.strftime("%d_%m_%Y_%H_%M")
            if loop == 0:
                pdb.set_trace()
                outfile_txt = f"{gparams.outdir}/{self.pair}.{self.timeframe}.{dt_str}.halist.txt"
                outfile_png = f"{gparams.outdir}/{self.pair}.{self.timeframe}.{dt_str}.halist.png"
                SRlst = calc_SR(sub_pvtlst, outfile=outfile_png)
                f = open(outfile_txt, 'w')
                res = SRlst.print()
                # print SR report to file
                f.write(res+"\n")
                f.close()
                tb_logger.info("Identified HAreaList for time {0}:".format(startO.isoformat()))
                tb_logger.info("{0}".format(res))
            elif loop >= tradebot_params.period:
                # An entire cycle has occurred. Invoke .calc_SR
                outfile_txt = f"{gparams.outdir}/{self.pair}.{self.timeframe}.{dt_str}.halist.txt"
                outfile_png = f"{gparams.outdir}/{self.pair}.{self.timeframe}.{dt_str}.halist.png"

                SRlst = calc_SR(sub_pvtlst, outfile=outfile_png)
                f = open(outfile_txt, 'w')
                res = SRlst.print()
                tb_logger.info("Identified HAreaList for time {0}:".format(startO.isoformat()))
                tb_logger.info("{0}".format(res))
                # print SR report to file
                f.write(res)
                f.close()
                loop = 0

            #  Fetch candle for current datetime. this is the current candle that
            # is being checked
            c_candle = self.clist.fetch_by_time(startO)
            if c_candle is None:
                startO = startO+delta
                loop += 1
                continue

            # c_candle.time is not equal to startO
            # when startO is non-working day, for example
            delta1hr = timedelta(hours=1)
            if (c_candle.time != startO) and (abs(c_candle.time-startO) > delta1hr):
                loop += 1
                tb_logger.info(f"Analysed dt {startO} is not the same than APIs returned dt {c_candle.time}."
                               " Skipping...")
                startO = startO + delta
                continue
            
            #check if there is any HArea overlapping with c_candle
            HAreaSel, sel_ix = SRlst.onArea(candle=c_candle)
            if HAreaSel is not None:
                # guess the if trade is 'long' or 'short'
                newCl = self.clist.slice(start=initc_date, end=c_candle.time)
                type = get_trade_type(c_candle.time, newCl)
                if tradebot_params.adj_SL == 'candles':
                    SL = adjust_SL_candles(type, newCl)
                elif tradebot_params.adj_SL == 'pips':
                    if type == 'short':
                        SL = adjust_SL_pips(c_candle.h, type, pair=self.pair)
                    else:
                        SL = adjust_SL_pips(c_candle.l, type, pair=self.pair)
                else:
                    SL, TP = adjust_SL_nextSR(SRlst, sel_ix, type)
                    if not SL:
                        if type == 'short':
                            SL = adjust_SL_pips(c_candle.h, type, pair=self.pair, no_pips=tradebot_params.adj_SL_pips)
                        else:
                            SL = adjust_SL_pips(c_candle.l, type, pair=self.pair, no_pips=tradebot_params.adj_SL_pips)
                prepare = False
                if c_candle.indecision_c(ic_perc=gparams.ic_perc) is True and len(SRlst.halist)>=3 and c_candle.height(pair=self.pair)<tradebot_params.max_height:
                    prepare = True
                elif type == 'short' and c_candle.colour == 'red' and len(SRlst.halist)>=3 and c_candle.height(pair=self.pair)<tradebot_params.max_height:
                    prepare = True
                elif type == 'long' and c_candle.colour == 'green' and len(SRlst.halist)>=3 and c_candle.height(pair=self.pair)<tradebot_params.max_height:
                    prepare = True

                # discard if IC falls on a Saturday
                if c_candle.time.weekday() == 5 and discard_sat is True:
                    tb_logger.info(f"Possible trade at {c_candle.time} falls on Sat. Skipping...")
                    prepare = False

                if prepare is True:
                    t = prepare_trade(
                        tb_obj=self,
                        type=type,
                        SL=SL,
                        TP=TP,
                        ic=c_candle,
                        harea_sel=HAreaSel,
                        delta=delta,
                        add_pips=tradebot_params.add_pips)
                    t.tot_SR = len(SRlst.halist)
                    t.rank_selSR = sel_ix
                    t.SRlst = SRlst
                    tlist.append(t)
                    res = validate_trade(t)
                    if not res:
                        raise Exception(f"Invalid TP, SL, entry configuration! for {t.start}. Type: {t.type}-{t.TP};{t.entry},{t.SL}")
            startO = startO+delta
            loop += 1

        tb_logger.info("Run done")

        return tlist