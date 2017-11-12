from __future__ import division
import pandas as pd
import pdb
import re
from OandaAPI import OandaAPI
from CandleList import CandleList

class TradeJournal(object):
    '''
    Constructor

    Class variables
    ---------------
    
    url: path to the .xlsx file with the trade journal
    '''

    def __init__(self, url):
        self.url=url
        #read-in the 'trading_journal' worksheet from a .xlsx file into a pandas dataframe
        xls_file = pd.ExcelFile(url)
        df = xls_file.parse('trading_journal')
        self.df=df

    def fetch_trades(self):

        trade_list=[]
        for index,row in self.df.iterrows():
            t=Trade(
                start=row['Start of trade'].to_pydatetime(),
                end=row['End of trade'].to_pydatetime(),
                pair=row['Currency Pair'],
                type=row['Type'],
                timeframe=row['Entry Time-frame']
                )
            trade_list.append(t)

        return trade_list


    def add_trend_momentum(self):
        '''
        This function will add a new worksheet named 'trend_momentum' to the .xlsx file
        For this, the function will perform some queries to the Oanda's REST API and will
        parse the results
        '''

        trade_list=self.fetch_trades()

        for trade in trade_list:
            oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                           instrument=trade.pair,
                           granularity=trade.timeframe,
                           alignmentTimezone='Europe/London',
                           start=trade.start.strftime('%Y-%m-%dT%H:%M:%S'),
                           dailyAlignment=22,
                           end=trade.end.strftime('%Y-%m-%dT%H:%M:%S'))

            candle_list=oanda.fetch_candleset()
            pdb.set_trace()
            cl=CandleList(candle_list)
            binary_seq_dict={
                'high': cl.get_binary_seq(trade.type,'high'), 
                'low': cl.get_binary_seq(trade.type,'low'),
                'open': cl.get_binary_seq(trade.type,'open'),
                'close': cl.get_binary_seq(trade.type,'close'),
                'colour': cl.get_binary_seq(trade.type,'colour')
                   }
            trade.binary_seq=binary_seq_dict
            number_of_0s_dict=trade.number_of_0s()
            #for high/lows
            double0s_highlow=trade.get_number_of_double0s(binary_seq_dict['high'],binary_seq_dict['low'])
            #for open/close
            double0s_openclose=trade.get_number_of_double0s(binary_seq_dict['open'],binary_seq_dict['close'])
            #get longest stretch
            trade.longest_stretch()
            print("h")
                                        

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
    binary_seq: dict, Optional
                Dictionary composed of 5 binary seqs used for analysing the trend
                momentum
                { 'high': '00100'
                  'low': '00010'
                  'open': '11111',
                  'close': '00000',
                  'colour': '000000'}
    number_of_0s_dict: dict, Optional
                       Dictionary composed of 5 numbers representing the number of 0s calculated with the
                       binary seqs from 'binary_seq'
                  
    '''

    def __init__(self, start, end, pair, type, timeframe):
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


    def number_of_0s(self, norm=True):
        '''
        This function will calculate the number of 0s
        in the binary sequence (i.e. 00100=4)

        Parameters
        ----------
        norm: bool, Optional
              If True then the returned value will
              be normalized by length. Default: True

        Returns
        -------
        A dict with the following structure:
        
         { 'high': 0.5
         'low': 1.0
         'open': 3.5
         'close': 4.2
         'colour': 4.7}
         
         Where the values are the number of 0s (possibly normalized)
        '''

        a_dict={}
        for key in self.binary_seq:
            sequence=self.binary_seq[key]
            a_list=list(sequence)
            new_list=[a_number for a_number in a_list if a_number=='0']
            number_of_0s=0
            if norm is True:
                number_of_0s=len(new_list)/len(a_list)
            else:
                number_of_0s=len(new_list)
            a_dict[key]=number_of_0s

        return a_dict

    def get_number_of_double0s(self,seq1,seq2,norm=True):
        '''
        This function will detect the columns having 2 0s in an alignment.
        For example:
        10100111
        11001000
        Will have 1 double 0

        Parameters
        ----------
        seq1: str, Required
        seq2: str, Required
        norm: bool, Optional
              If True then the returned value will
              be normalized by length. Default: True

        Returns
        -------
        A float
        '''
        list1=list(seq1)
        list2=list(seq2)

        if len(list1) != len(list2):
            raise Exception("Lengths of seq1 and seq2 are not equal")

        number_of_double0s=0
        for i, j in zip(list1, list2):
            if int(i)==0 and int(j)==0:
                number_of_double0s=number_of_double0s+1
                
        if norm is True:
            return number_of_double0s/len(list1)
        else:
            return number_of_double0s

    def longest_stretch(self):
        '''
        This function will calculate the longest stretch of contiguous 0s.
        
        For example:
        1010000111
        
        Will return 4

        Returns
        -------
        A dict with the following structure:

        { 'high': 2
          'low': 4
          'open': 3
          'close': 2
          'colour': 4}

        Where the values represent the longest stretch of 0s
        '''
        a_dict={}
        for key in self.binary_seq:
            sequence=self.binary_seq[key]
            length=len(max(re.compile("(0+0)*").findall(sequence)))
            a_dict[key]=length

        return a_dict

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
