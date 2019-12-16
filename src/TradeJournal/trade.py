from __future__ import division
import datetime
import pdb
import re
import config
import warnings
from oanda_api import OandaAPI
from candlelist import CandleList
from harea import HArea
from utils import *

class Trade(object):
    '''
    This class represents a single row from the dataframe in the TradeJournal class

    Class variables
    ---------------

    trend_i: datetime, Optional
             start of the trend
    start: datetime, Required
           Time/date when the trade was taken. i.e. 20-03-2017 08:20:00s
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    outcome: str, Optional
             Outcome of the trade. Possible values are: success, failure, breakeven
    end: datetime, Optional
         Time/date when the trade ended. i.e. 20-03-2017 08:20:00
    entry: float, Optional
           entry price
    entry_time: datetime.optional
                Datetime for price reaching the entry price
    type: str, Optional
          What is the type of the trade (long,short)
    SL:  float, Optional
         Stop/Loss price
    TP:  float, Optional
         Take profit price
    SR:  float, Optional
         Support/Resistance area
    pips:  int, Optional
           Number of pips of profit/loss. This number will be negative if outcome was failure
    strat: string, Required
           What strategy was used for this trade. Possible values are defined in config.py
    id : str, Required
         Id used for this object
    '''

    def __init__(self, strat, **kwargs):

        self.__dict__.update(kwargs)

        self.strat=strat
        self.pair=re.sub('/','_',self.pair)
        #remove potential whitespaces in timeframe
        self.timeframe=re.sub(' ','',self.timeframe)

    def fetch_candlelist(self):
        '''
        This function returns a CandleList object for this Trade

        Returns
        -------

        A CandleList object

        '''
        oanda = OandaAPI(url=config.OANDA_API['url'],
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone=config.OANDA_API['alignmentTimezone'],
                         dailyAlignment=config.OANDA_API['dailyAlignment'])

        oanda.run(start=datetime.datetime.strptime(self.start,'%Y-%m-%dT%H:%M:%S').isoformat(),
                  end=datetime.datetime.strptime(self.end,'%Y-%m-%dT%H:%M:%S').isoformat(),
                  roll=True)

        candle_list=oanda.fetch_candleset()
        cl=CandleList(candle_list, type=self.type)

        return cl

    def run_trade(self):
        '''
        Run the trade until conclusion from a start date
        '''

        print("[INFO] Run run_trade with id: {0}".format(self.id))

        entry = HArea(price=self.entry,pips=1, instrument=self.pair, granularity=self.timeframe)
        SL = HArea(price=self.SL,pips=1, instrument=self.pair, granularity=self.timeframe)
        TP = HArea(price=self.TP, pips=1, instrument=self.pair, granularity=self.timeframe)

        period=None
        if self.timeframe == "D":
            period=24
        else:
            period = int(self.timeframe.replace('H', ''))

        # generate a range of dates starting at self.start and ending numperiods later in order to assess the outcome
        # of trade and also the entry time

        self.start=datetime.datetime.strptime(str(self.start),'%Y-%m-%d %H:%M:%S')
        numperiods=300
        date_list = [datetime.datetime.strptime(str(self.start.isoformat()),'%Y-%m-%dT%H:%M:%S') + datetime.timedelta(hours=x*period) for x in range(0, numperiods)]

        entered=False
        for d in date_list:
            oanda = OandaAPI(url=config.OANDA_API['url'],
                             instrument=self.pair,
                             granularity=self.timeframe,
                             dailyAlignment=config.OANDA_API['dailyAlignment'],
                             alignmentTimezone=config.OANDA_API['alignmentTimezone'])

            oanda.run(start=d.isoformat(),
                      count=1,
                      roll=True)

            cl=oanda.fetch_candleset()[0]

            if entered is False:
                entry_time = entry.get_cross_time(candle=cl)
                warnings.warn("\t[INFO] Trade entered")
                if entry_time!='n.a.':
                    self.entry_time = entry_time.isoformat()
                else:
                    warnings.warn("No entry time was identified for this trade")
                    entry_time=self.start
                    self.entry_time = entry_time
            if entry_time is not None and entry_time != 'n.a.':
                entered=True
            if entered is True:
                failure_time = SL.get_cross_time(candle=cl)
                if failure_time is not None and failure_time != 'n.a.':
                    self.outcome='failure'
                    self.end = failure_time
                    self.pips=float(calculate_pips(self.pair,abs(self.SL-self.entry)))*-1
                    warnings.warn("\t[INFO] S/L was hit")
                    break
            if entered is True:
                success_time = TP.get_cross_time(candle=cl)
                if success_time is not None and success_time !='n.a.':
                    self.outcome = 'success'
                    warnings.warn("\t[INFO] T/P was hit")
                    self.end=success_time
                    self.pips = float(calculate_pips(self.pair, abs(self.TP - self.entry)))
                    break
        try:
            assert getattr(self, 'outcome')
        except:
            warnings.warn("\tNo outcome could be calculated")
            self.outcome="n.a."
            self.pips="n.a."

        warnings.warn("[INFO] Done run_trade")

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
