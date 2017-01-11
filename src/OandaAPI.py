'''
Created on 24 Nov 2016

@author: ernesto
'''

import re
import os
import requests,json
import pandas as pd
from pandas.tseries.offsets import BDay
from matplotlib.finance import volume_overlay
from datetime import datetime,timedelta
import datetime

class Candle(object):
    '''
    Constructor

    Class variables
    ---------------
    representation : str, either 'midpoint' or 'bidask'
           The candle's representation type
    time : datetime
        Candle's date and time
    volume : int
        Candle's volume
    complete : boolean
        Is the candle complete?  
    formation : candle formation
        Possible values are: 
    '''

    def __init__(self, representation=None, time=None, volume=0, complete=True, formation=None):
        self.representation=representation
        self.time=time
        self.volume=volume
        if complete not in [True, False] : raise Exception(("complete %s is not valid. Complete should be True or False")) % complete
        self.complete=complete
        self.formation=formation
        
        
class MidPointCandle(Candle):
    '''
    Constructor

    Class variables
    ---------------
    bam : str
          Path to BAM file
          
    Inherits from Candle
    '''
    
class BidAskCandle(Candle):
    '''
    Constructor

    Class variables
    ---------------
    openBid : float
              Candle's openBid value
    openAsk : float
              Candle's openAsk value
    highBid : float
              Candle's highBid value
    highAsk : float
              Candle's highAsk value
    lowBid  : float
              Candle's lowBid value
    lowAsk  : float
              Candle's lowAsk value
    closeBid : float
               Candle's lowAsk value
    closeAsk : float
               Candle's closeAsk value
          
    Inherits from Candle
    '''
    
    def __init__(self, representation=None, openBid=None, openAsk=None, highBid=None, highAsk=None, 
                 lowBid=None, lowAsk=None, closeBid=None, closeAsk=None, upper_wick=None, lower_wick=None
                 ,colour=None):
        Candle.__init__(self,representation)
        self.openBid=openBid
        self.openAsk=openAsk
        self.highBid=highBid
        self.highAsk=highAsk
        self.lowBid=lowBid
        self.lowAsk=lowAsk
        self.closeBid=closeBid
        self.closeAsk=closeAsk
        self.colour=colour
        self.upper_wick=upper_wick
        self.lower_wick=lower_wick
    
    def set_candle_features (self):
        '''
        Set basic candle features based on price
        i.e. self.colour, upper_wick, etc...
        
        Returns
        ------
        None
        
        '''
        if not self.openBid or not self.closeBid:
            raise Exception("Either self.openBid or self.closeBid need to be set to invoke set_candle_pattern")
        
        if not self.highBid or not self.lowBid:
            raise Exception("Either self.highBid or self.lowBid need to be set to invoke set_candle_pattern")
        
        upper=lower=0.0
        if self.openBid < self.closeBid:
            self.colour="green"
            upper=self.closeBid
            lower=self.openBid
        elif self.openBid > self.closeBid:
            self.colour="red"
            upper=self.openBid
            lower=self.closeBid
        else:
            raise Exception("undefined colour")
        
        self.upper_wick=self.highBid-upper
        self.lower_wick=lower-self.lowBid
    
    def set_candle_formation (self):
        '''
        Set candle formation 
        
        Note: These are the conventions I will follow:
        
        DOJI: Body is <=10% of the total candle height
        
        Returns
        ------
        None
        
        '''
        if self.openBid is None or self.closeBid is None:
            raise Exception("Either self.openBid or self.closeBid need to be set to invoke set_candle_pattern")
        
        if self.highBid is None or self.lowBid is None:
            raise Exception("Either self.highBid or self.lowBid need to be set to invoke set_candle_pattern")
        
        if self.upper_wick is None or self.lower_wick is None:
            raise Exception("Either self.upper_wick or self.lower_wick need to be set to invoke set_candle_formation")
        
        height=self.highBid-self.lowBid
        body=abs(self.openBid-self.closeBid)
        
        perc_body=(body*100)/height
        perc_uwick=(self.upper_wick*100)/height
        perc_lwick=(self.lower_wick*100)/height
        
        if perc_body<35 and perc_lwick>60 and self.colour=="green":
            self.representation="hammer"
        elif perc_body<35 and perc_lwick>60 and self.colour=="red":
            self.representation="hanging_man"
        elif perc_body<40 and perc_uwick>55 and self.colour=="green":
            self.representation="inverted_hammer"
        elif perc_body<40 and perc_uwick>55 and self.colour=="red":
            self.representation="shooting_star"
        elif perc_body<4 and perc_uwick>40 and perc_lwick>40:
            self.representation="doji"
        elif perc_body<4 and perc_uwick<2 and perc_lwick>94:
            self.representation="dragonfly_doji"
        elif perc_body<4 and perc_uwick>94 and perc_lwick<2:
            self.representation="gravestone_doji"
        elif perc_body>90 and self.colour=="green":
            self.representation="green_marubozu"
        elif perc_body>90 and self.colour=="red":
            self.representation="red_marubozu"
        else:
            self.representation="undefined"
        
    def __repr__(self):
        return "BidAskCandle"
    
    def __str__(self):
        out_str=""
        for attr, value in self.__dict__.iteritems():
            out_str+="%s:%s " %(attr, value)
        return out_str
            
class OandaAPI(object):
    '''
    Class representing the content returned by a GET request to Oanda's REST API
    '''
    
    def __init__(self, url=None, data=None, **params):
        '''
        Constructor

         Class variables
        ---------------
        url : string
              Oanda's REST service url
        data : object
               Deserialized content returned by requests' 'get'
        params : dict
               Dictionary with parameters to pass to requests
        resp : object
               returned by requests module
        instrument: str
        '''
        if url:
            resp = requests.get(url=url,params=params)
        
            self.resp=resp
        
            if resp.status_code != 200:
                 # This means something went wrong.
                 raise Exception('GET /candles {}'.format(resp.status_code))
    
            if data:
                self.data=data
            else:
                self.data = json.loads(resp.content)
            
    def print_url(self):
        '''
        Print url from requests module
        '''
        
        print "URL: %s" % self.resp.url
        
    def fetch_candleset(self):
        '''
        Retrieve candles in self.data
        
        Returns
        ------
        A list of Candle objects
        
        '''
        candlelist=[]
        
        for c in self.data['candles']:
            
            if "openBid" in c:
                
                cd=BidAskCandle(representation="bidask")
                for k,v in c.items():
                    if k=="time":
                        pd.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%fZ')
                        setattr(cd,k,pd.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%fZ'))
                    else:
                        setattr(cd,k,v)
                candlelist.append(cd)
        return candlelist
    
    def fetch_candles_from_file(self, file):
        '''
        Retrieves candles from file
        
        Returns
        ------
        A list of Candle objects
        
        '''
        
        if os.path.isfile(file) == False:
            raise Exception("File does not exist")
        
        candlelist=[]
        
        with open(file) as f:
            for line in f:
                line=line.rstrip("\n")
                bits=line.split()
                regex=re.compile("highAsk:*")
                a_list=[m.group(0) for l in bits for m in [regex.search(l)] if m]
                if len(a_list)>0:
                    ba=BidAskCandle()
                    for b in bits:
                        l=b.split(':')
                        if len(l)==2:
                            setattr(ba, l[0], l[1])
                    candlelist.append(ba)
        return candlelist
         
class Reversal(object):
    '''
    Class representing a potential price reversal
    '''
    
    def __init__(self, ic,outcome,number_pre,number_post,instrument,granularity='D',pre_candles=None,post_candles=None):
        '''
        Constructor

         Class variables
        ---------------
        ic : str
             String representing the time of the indecision candle
        outcome : boolean
             Was reversal successful?
        number_pre : int
             Number of candles before the indecision candle (excluding it)
        number_post : int
             Number of candles after the indecision candle (excluding it)
        instrument : str
            i.e. AUD_USD
        granularity : str, default = D
             Timeframe to use (i.e. D, H12)
        pre_candles : list, optional
             List of candles before the possible reversal (before the IC)
        post_candles : list, optional
             List of candles after the possible reversal (after the IC)
        '''
        self.ic=ic
        self.outcome=outcome
        self.number_pre=number_pre
        self.number_post=number_post
        self.instrument=instrument
        self.granularity=granularity
        self.pre_candles=pre_candles
        self.post_candles=post_candles
        
        delta=""
        freq=""
        if self.granularity=='D':
            delta=timedelta(days=1)
            freq="D"
        else:
            m = re.search("H(\d+)",self.granularity)
            if m:
                delta=timedelta(hours=int(m.groups()[0]))
                freq="%sH" % m.groups()[0]
                
        if not delta: raise Exception("Granularity %s is in a non valid format" % self.granularity)
        
        candle = pd.datetime.strptime(ic, "%Y-%m-%d %H:%M:%S")
        
        start=candle-self.number_pre*delta
        end=candle+self.number_post*delta
        
        for d in pd.date_range(start=start,end=candle, freq=freq):
            if (d.weekday()==4 and d.time()==datetime.time(22,0,0)) or d.weekday()==5 or (d.weekday()==6 and d.time()<datetime.time(22, 0, 0)):
                start=start-delta
                
        if start.weekday()==4 and start.time()==datetime.time(22,0,0):
            start=start-delta
        
        for d in pd.date_range(start=candle+delta,end=end, freq=freq):
            if (d.weekday()==4 and d.time()==datetime.time(22,0,0)) or d.weekday()==5 or (d.weekday()==6 and d.time()<datetime.time(22, 0, 0)):
                end=end+delta
                
        if end.weekday()==5:
            end=end+delta
        
        oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',instrument=self.instrument,granularity=self.granularity,alignmentTimezone='Europe/London',dailyAlignment=22,start=start.isoformat(),end=end.isoformat())
    
        '''
        oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',instrument=self.instrument,granularity=self.granularity,alignmentTimezone='Europe/London',dailyAlignment=22,start=start.isoformat(),count=5)
        '''
        
        candlelist=oanda.fetch_candleset()

        for c in candlelist:
            c.set_candle_features()
            c.set_candle_formation()
            print(c)
        
        
        
        '''
        if colors:
            self.colors=colors
        else:
            self.colors=[]
            for c in candles:
                c.set_candle_features
                self.colors.append(c.colour)
         ''' 
