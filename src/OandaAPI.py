'''
Created on 24 Nov 2016

@author: ernesto
'''

import pdb
import re
import os
import requests,json
import pandas as pd
from pandas.tseries.offsets import BDay
from matplotlib.finance import volume_overlay
from datetime import datetime,timedelta
import datetime
import pytz
#from pandas.stats.tests.common import start

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
        self.formation=format
        
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
                 ,colour=None,perc_body=None,perc_uwick=None,perc_lwick=None):
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
        self.perc_body=perc_body
        self.perc_uwick=perc_uwick
        self.perc_lwick=perc_lwick
    
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
            self.colour="undefined"
            upper=self.openBid
            lower=self.closeBid
        
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
        
        self.perc_body=perc_body
        self.perc_uwick=perc_uwick
        self.perc_lwick=perc_lwick
        
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
        for attr, value in self.__dict__.items():
            out_str+="%s:%s " %(attr, value)
        return out_str
            
class BiCandle:
    '''
    Constructor
    
    This class represents any combination of two candles

    Class variables
    ---------------
    
    candleA: BidAskCandle object
             First candle in the pair
    candleB: BidAskCandle object
             Second candle in the pair
    '''
    def __init__(self, candleA, candleB):
        self.candleA=candleA
        self.candleB=candleB
        
    def is_engulfing(self):
        '''
        Does candleB engulfs candleA?. Engulfing happens when candleB body engulfs the whole
        candleA (including the body and the wicks)
        
        Returns
        ------
        True or False
        '''
        
        if self.candleB.openBid>self.candleA.highBid and self.candleB.closeBid<self.candleA.lowBid:
            return True
        else:
            return False


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
                 print("Something went wrong. url used was:\n{0}".format(resp.url))
                 raise Exception('GET /candles {}'.format(resp.status_code))
    
            if data:
                self.data=data
            else:
                 self.data = json.loads(resp.content.decode("utf-8"))
            
    def print_url(self):
        '''
        Print url from requests module
        '''
        
        print("URL: %s" % self.resp.url)
        
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
    
    def __is_market_closed(self,dt):
        '''
        Private method to check if the datetime object falls within a period when marked it closed
        
        dt  datetime object
        
        Returns
        -------
        Boolean    True is market is closed
        
        '''
        if (dt.weekday()==4 and dt.time()==datetime.time(22,0,0)):
            return True
        elif (dt.month==12 and dt.day==24 and dt.time()>=datetime.time(22,0,0)):
            return True
        elif (dt.month==12 and dt.day==25):
            return True
        elif (dt.month==12 and dt.day==26 and dt.time()<datetime.time(22, 0, 0)):
            return True
        elif (dt.month==12 and dt.day==31 and dt.time()>=datetime.time(22, 0, 0)):
            return True
        elif (dt.month==1 and dt.day==1 and dt.time()<datetime.time(22, 0, 0)):
            return True
        elif (dt.weekday()==5 or (dt.weekday()==6 and dt.time()<datetime.time(22, 0, 0))):
            return True
        else:
            return False

    def __offset_closed_marked(self,start,end,freq,delta,dir):
        '''
        This private function will check a period between 2 dates and will extend start/end depending on a particular date falling
        on a day when the market is closed
        
        start: datetime object
            Start of the period that will be checked
        end: datetime object
            End of the period that will be checked
        freq: str
            Time frequency to increase the intervals. eg 'D', 'H12', ...
        delta: timedelta object 
            Used for the offset
        dir: str, 'L'/'R'
            Direction of interval extension. 
        '''
        '''
        for d in pd.date_range(start=start,end=end, freq=freq):
            if self.__is_market_closed(d)==True:
                if dir=='L':
                    start=start-delta
                elif dir=='R':
                    end=end+delta
                if dir=='L':
                    while (start.weekday()==4 and start.time()>=datetime.time(21,0,0)) or start.weekday()==5 or (start.weekday()==6 and start.time()<datetime.time(21, 0, 0)):
                        start=start-delta
                elif dir=='R':
                    while (end.weekday()==4 and end.time()>=datetime.time(22,0,0)) or end.weekday()==5 or (end.weekday()==6 and end.time()<datetime.time(21, 0, 0)):
                        end=end+delta
        '''
        for d in pd.date_range(start=start,end=end, freq=freq):
            if self.__is_market_closed(d)==True:
                if dir=='L':
                    start=start-delta
                elif dir=='R':
                    end=end+delta
                if dir=='L':
                    while (self.__is_market_closed(start)):
                        start=start-delta
                elif dir=='R':
                    while (self.__is_market_closed(end)):
                        end=end+delta
        if dir=='L':
             return start
        elif dir=='R':
             return end
    
    def __check_correctness(self,obs_len,exp_len,exp_ic,obs_ic):
        '''
        Function to check if the candlelist returned by the Oanda API is correct
        in terms of length and indecision candle
        
        Parameters
        ----------
        obs_len: int, Required
                 Observed list length of the candlelist
        exp_len: int, Required
                 Expected list length as determined by the number_pre+number_post+ic
        exp_ic: datetime object, Required
                 Indecision candle as requested in the ic_candle class member of the Reversal object
        obs_ic: datetime object, Required
                 Observed Indecision candle.       
        '''
        
        if obs_len!=exp_len:
            raise Exception("candlelist length is not correct for %s!\nexpected: %d\nobserved: %d" % (exp_ic,exp_len,obs_len))
        
        if exp_ic!=obs_ic:
            raise Exception("ind. candle  is not correct:\n expected %s\nobserved %s!" % (exp_ic,obs_ic))
     
    def __is_dst(self,timezone,time):
         '''
         Function to know if a particular candle time is in the daylight savings period
         
         Parameters
        ----------
         timezone: str, Required
                   i.e. 'Europe/London','America/New_York'
         time: datetime object 
         
         Returns
         -------
         Boolean, True means that the datetime is in the dst scheme
         
         '''
         timezone=pytz.timezone(timezone)
         dst_candle=timezone.localize(time, is_dst=None)
         
         return bool (dst_candle.dst())
 

    def __init__(self,type,ic,outcome,number_pre,number_post,instrument,granularity='D',pre_candles=None,post_candles=None):
        '''
        Constructor

         Class variables
        ---------------
        type: str, [bullish or bearish]
             Type of reversal
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
        ic_candle : Candle object, optional
             Indecission candle
        post_candles : list, optional
             List of candles after the possible reversal (after the IC)        
        '''
        self.type=type
        self.ic=ic
        self.outcome=outcome
        self.number_pre=number_pre
        self.number_post=number_post
        self.instrument=instrument
        self.granularity=granularity
        self.pre_candles=pre_candles
        self.post_candles=post_candles
        
        if type!="bullish" and type!="bearish":
            raise Exception("type of candle %s is not valid for %s! Valid types are bullish or bearish" % (ic,type))
        
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
        
        delta_10min=timedelta(minutes=10) 
        
        if self.__is_market_closed(candle)==True:
            raise Exception("IC %s cannot be used!. Market is closed"% ic)

        start=candle-self.number_pre*delta
        end=candle+self.number_post*delta
        
        start=self.__offset_closed_marked(start,candle,freq,delta,'L')
        end=self.__offset_closed_marked(candle+delta,end,freq,delta,'R')
                
        l_lnd=[self.__is_dst('Europe/London',x) for x in [start,candle,end]]
        l_ny=[self.__is_dst('America/New_York',x) for x in [start,candle,end]]
        
        if l_lnd!=l_ny:
            raise Exception("Discrepancy in the DST. %s remove IC" % ic)
        elif len(set(l_lnd))>1 or len(set(l_ny)) > 1:
            raise Exception("Discrepancy in the DST. %s remove IC" % ic)
        
        '''correct for dst'''
        dailyAlignment=22
        
        if list(set(l_lnd))[0]==True:
            dailyAlignment+=1
        
        oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',instrument=self.instrument,granularity=self.granularity,alignmentTimezone='Europe/London',dailyAlignment=dailyAlignment,start=start.isoformat(),end=(end+delta_10min).isoformat())
        
        candlelist=oanda.fetch_candleset()
        
        newlist = [x for x in candlelist if self.__is_market_closed(x.time)==False]
        
        for c in newlist:
            c.set_candle_features()
            c.set_candle_formation()
 
        '''
        check if candlelist is correct
        '''
        
        total=number_pre+number_post+1
        middle=number_pre+1
       
        self.__check_correctness(obs_len=len(newlist),exp_len=total,exp_ic=candle,obs_ic=newlist[middle-1].time)   

        middle=number_pre+1
        self.pre_candles=newlist[:number_pre]
        self.ic_candle=newlist[middle-1]
        self.post_candles=newlist[middle:]
        
    def get_differential(self,candlelist,select,entity):
        '''
        Method to get the difference in the price between the current upper/lower wick/candle and the previous one
        
        Parameters
        ----------
        candlelist: list
                    List of candles
        select : str, [upper, lower] required
                 Calculate the different between highs (upper), lows (lower)
        entity : str, [wick, candle] required
                 Calculate the differential on the wick or the candle
        
        Return
        ------
        List of floats with the difference between the highs/lows
        '''
        
        p_candle=0.0
        l=[]
        
        for k,i in enumerate(candlelist):
            val=0.0
            if select=="upper":
                if entity=="wick":
                    val=i.highBid
                elif entity=="candle":
                    val=i.openBid
            elif select=="lower":
                if entity=="wick":
                    val=i.lowBid
                elif entity=="candle":
                    val=i.closeBid
            else:
                raise Exception("select argument %s is not recognised" % select)         
            
            if(k==0):
                p_candle=float(val)
            else:
                c_candle=float(val)-p_candle
                l.append(c_candle)
                p_candle=float(val)
        return l
