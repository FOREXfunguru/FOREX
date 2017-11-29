from __future__ import division
import pandas as pd
import pdb
import re
from OandaAPI import OandaAPI
from CandleList import CandleList


class Trade(object):
    '''
    This class represents a single row from the dataframe in the TradeJournal class

    Class variables
    ---------------
    
    start: datetime, Required
           Time/date when the trade was taken. i.e. 20-03-2017 08:20:00
    end: datetime, Required
         Time/date when the trade ended. i.e. 20-03-2017 08:20:00
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    type: str, Required
          Type of trade. Possible values are 'long'/'short'
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    outcome: str, Required
             Outcome of the trade. Possible values are: success, failure, breakeven
    '''

    def __init__(self, start, end, pair, type, timeframe, outcome):
        self.start=start
        self.end=end
        self.pair=re.sub('/','_',pair)
        if type=='bearish':
            self.type='short'
        elif type=='bullish':
            self.type='long'
        else:
            raise Exception("{0} is not a valid Trade type".format(type))
        self.timeframe=timeframe
        self.outcome=outcome

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
                       start=self.start.strftime('%Y-%m-%dT%H:%M:%S'),
                       dailyAlignment=22,
                       end=self.end.strftime('%Y-%m-%dT%H:%M:%S'))

        candle_list=oanda.fetch_candleset()
        cl=CandleList(candle_list, type=self.type)

        return cl

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
