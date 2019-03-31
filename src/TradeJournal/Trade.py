from __future__ import division
import datetime
import pdb
import re
from OandaAPI import OandaAPI
from CandleList import CandleList
from HArea import HArea

class Trade(object):
    '''
    This class represents a single row from the dataframe in the TradeJournal class

    Class variables
    ---------------

    trend_i: start of the trend conducting to the entry of 1st peak
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
    type: str, Optional
          What is the type of the trade (long,short)
    SL:  float, Optional
         Stop/Loss price
    TP:  float, Optional
         Take profit price
    SR:  float, Optional
         Support/Resistance area
    strat: string, Required
           What strategy was used for this trade. Possible values are: 'counter','cont','ctdbtp'
    '''

    def __init__(self, start, pair, timeframe, type=None, end=None, outcome=None, entry=None,
                 SL=None, TP=None, SR=None, strat=None, trend_i=None):
        self.trend_i = trend_i
        self.start=start
        self.pair=re.sub('/','_',pair)
        self.timeframe = timeframe
        self.type=type
        self.end = end
        self.outcome=outcome
        self.entry=entry
        self.SL=SL
        self.TP=TP
        self.SR=SR
        self.strat=strat



    def fetch_candlelist(self):
        '''
        This function returns a CandleList object for this Trade

        Returns
        -------

        A CandleList object

        '''
        oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                       instrument=self.pair,
                       granularity=self.timeframe,
                       alignmentTimezone='Europe/London',
                       start=datetime.datetime.strptime(self.start,'%Y-%m-%dT%H:%M:%S').isoformat(),
                       dailyAlignment=22,
                       end=datetime.datetime.strptime(self.end,'%Y-%m-%dT%H:%M:%S').isoformat())

        candle_list=oanda.fetch_candleset()
        cl=CandleList(candle_list, type=self.type)

        return cl

    def run_trade(self):
        '''
        Run the trade until conclusion from a start date
        '''

        entry = HArea(price=self.entry,pips=1, instrument=self.pair, granularity=self.timeframe)
        SL = HArea(price=self.SL,pips=1, instrument=self.pair, granularity=self.timeframe)
        TP = HArea(price=self.TP, pips=1, instrument=self.pair, granularity=self.timeframe)

        period=None
        if self.timeframe == "D":
            period=24
        else:
            period = int(self.timeframe.replace('H', ''))

        numperiods=100
        date_list = [datetime.datetime.strptime(self.start,'%Y-%m-%dT%H:%M:%S') + datetime.timedelta(hours=x*period) for x in range(0, numperiods)]

        entered=False
        for d in date_list:
            oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                             instrument=self.pair,
                             granularity=self.timeframe,
                             dailyAlignment=22,
                             alignmentTimezone='Europe/London',
                             start=d.isoformat(),
                             count=1)
            cl=oanda.fetch_candleset()[0]

            entry_time = entry.get_cross_time(candle=cl)
            if entry_time is not None:
                entered=True
            if entered is True:
                failure_time = SL.get_cross_time(candle=cl)
                if failure_time is not None:
                    self.outcome='failure'
                    self.end = failure_time
                    break
            if entered is True:
                success_time = TP.get_cross_time(candle=cl)
                if success_time is not None:
                    self.outcome = 'success'
                    self.end=success_time
                    break

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
