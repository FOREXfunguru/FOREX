import logging
import pdb
import datetime
from datetime import datetime
import pandas as pd

from api.oanda.connect import Connect
from forex.candle import Candle
from forex.params import tradebot_params, gparams
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
        start: Datetime that this Bot will start operating. i.e. 20-03-2017 08:20:00s
        end: Datetime that this Bot will end operating. i.e. 20-03-2020 08:20:00s
        pair: Currency pair used in the trade. i.e. AUD_USD
        timeframe: Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4,H1
    '''
    def __init__(self, start:datetime, end:datetime, pair:str, timeframe:str):
        self.start = start
        self.end = end
        self.pair = pair
        self.timeframe = timeframe

    def run(self, discard_sat=True):
        '''This function will run the Bot from start to end
        one candle at a time.

        Arguments:
            discard_sat: If this is set to True, then the Trade wil not
                         be taken if IC falls on a Saturday

        Returns:
            TradeList object with Trades taken. None if no trades
            were taken
        '''
        tb_logger.info("Running...")
        conn = Connect(instrument=self.pair,
                       granularity=self.timeframe)

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

        # convert to datetime the start and end for this TradeBot
        startO = pd.datetime.strptime(self.start, '%Y-%m-%d %H:%M:%S')
        endO = pd.datetime.strptime(self.end, '%Y-%m-%d %H:%M:%S')

        loop = 0
        tlist = []
        tend = SRlst = None
        # calculate the start datetime for the CList that will be used
        # for calculating the S/R areas
        delta_period = periodToDelta(tradebot_params.period_range,
                                     self.timeframe)
        initc_date = startO-delta_period
        # Get now a CandleList from 'initc_date' to 'startO' which is the
        # total time interval for this TradeBot
        clO = conn.query(start=initc_date.isoformat(),
                         end=endO.isoformat())

        while startO <= endO:
            """
            if tend is not None:
                # this means that there is currently an active trade
                if startO <= tend:
                    startO = startO + delta
                    loop += 1
                    continue
                else:
                    tend = None
            """
            tb_logger.info("Trade bot - analyzing candle: {0}".format(startO.isoformat()))
            subclO = clO.slice(initc_date, startO)
            sub_pvtlst = PivotList(clist=subclO)
            dt_str = startO.strftime("%d_%m_%Y_%H_%M")
            if loop == 0:
                outfile_txt = f"{gparams.outdir}/{self.pair}.{self.timeframe}.{dt_str}.halist.txt"
                outfile_png = f"{gparams.outdir}/{self.pair}.{self.timeframe}.{dt_str}.halist.png"
                SRlst = calc_SR(sub_pvtlst, outfile=outfile_png)
                f = open(outfile_txt, 'w')
                res = SRlst.print()
                # print SR report to file
                f.write(res)
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
            c_candle = conn.query(start=startO.isoformat(),
                                  count=1).candles[0]

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
                newCl = clO.slice(start=initc_date, end=c_candle.time)
                type = get_trade_type(c_candle.time, newCl)
                SL = adjust_SL(type, newCl)
                prepare = False
                if c_candle.indecision_c(ic_perc=gparams.ic_perc) is True:
                    prepare = True
                elif type == 'short' and c_candle.colour == 'red':
                    prepare = True
                elif type == 'long' and c_candle.colour == 'green':
                    prepare = True

                # discard if IC falls on a Saturday
                if c_candle.time.weekday() == 5 and discard_sat is True:
                    tb_logger.info(f"Possible trade at {c_candle.time} falls on Sat. Skipping...")
                    prepare = False

                if prepare is True:
                    pdb.set_trace()
                    t = prepare_trade(
                        tb_obj=self,
                        type=type,
                        SL=SL,
                        ic=c_candle,
                        harea_sel=HAreaSel,
                        delta=delta,
                        add_pips=tradebot_params.add_pips)
                    t.tot_SR = len(SRlst.halist)
                    t.rank_selSR = sel_ix
                    t.SRlst = SRlst
                    tlist.append(t)
            startO = startO+delta
            loop += 1

        tb_logger.info("Run done")

        if len(tlist) == 0:
            return None
        else:
            return tlist

class TradeDiscover(object):
    '''
    This class represents an automatic Trading bot to discover new trades

    Class variables
    ---------------
    start : datetime
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    '''
    def __init__(self, start, pair, timeframe):
        self.start = start
        self.pair = pair
        self.timeframe = timeframe

    def run(self):
        """
        Run the bot from self.start

        Returns
        -------
        Trade object or none
        """
        tb_logger.info("Running...")

        conn = Connect(instrument=self.pair,
                       granularity=self.timeframe)

        ser_dir = None
        if CONFIG.has_option('general', 'ser_data_dir'):
            ser_dir = CONFIG.get('general', 'ser_data_dir')

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

        # calculate the start datetime for the CList that will be used
        # for calculating the S/R areas
        delta_period = periodToDelta(CONFIG.getint('trade_bot', 'period_range'),
                                     self.timeframe)

        initc_date = self.start - delta_period
        # Get now a CandleList from 'initc_date' to 'startO' which is the
        # total time interval for this TradeBot
        clO = conn.query(start=initc_date.strftime("%Y-%m-%dT%H:%M:%S"),
                         end=self.start.strftime("%Y-%m-%dT%H:%M:%S"))
        dt_str = self.start.strftime("%d_%m_%Y_%H_%M")
        outfile_png = "{0}/srareas/{1}.{2}.{3}.halist.png".format(CONFIG.get("images", "outdir"),
                                                                  self.pair, self.timeframe, dt_str)
        SRlst = calc_SR(clO, outfile=outfile_png)

        # fetch candle for current datetime
        res = conn.query(start=self.start.strftime("%Y-%m-%dT%H:%M:%S"),
                         count=1,
                         indir=ser_dir)

        # this is the current candle that
        # is being checked
        c_candle = Candle(dict_data=res['candles'][0])
        c_candle.time = datetime.strptime(c_candle.time,
                                          '%Y-%m-%dT%H:%M:%S.%fZ')

        # check if there is any HArea overlapping with c_candle
        HAreaSel, sel_ix = SRlst.onArea(candle=c_candle)

        if HAreaSel is not None:
            c_candle.set_candle_features()
            # guess the if trade is 'long' or 'short'
            newCl = clO.slice(start=initc_date, end=c_candle.time)
            type = get_trade_type(c_candle.time, newCl)
            SL = adjust_SL(type, newCl, CONFIG.getint('trade_bot', 'n_SL'))
            prepare = False
            if c_candle.indecision_c(ic_perc=CONFIG.getint('general', 'ic_perc')) is True:
                prepare = True
            elif type == 'short' and c_candle.colour == 'red':
                prepare = True
            elif type == 'long' and c_candle.colour == 'green':
                prepare = True

            # discard if IC falls on a Saturday
            if c_candle.time.weekday() == 5 and discard_sat is True:
                tb_logger.info("Possible trade at {0} falls on Sat. Skipping...".format(c_candle.time))
                prepare = False

            t = None
            if prepare is True:
                t = prepare_trade(
                    tb_obj=self,
                    type=type,
                    SL=SL,
                    ic=c_candle,
                    harea_sel=HAreaSel,
                    delta=delta,
                    add_pips=CONFIG.getint('trade', 'add_pips'))
                t.tot_SR = len(SRlst.halist)
                t.rank_selSR = sel_ix
                t.SRlst = SRlst
            return t
        tb_logger.info("Run done")

