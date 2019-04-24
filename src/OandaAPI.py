'''
Created on 24 Nov 2016

@author: ernesto lowy
'''

import pdb
import re
import os
import requests,json
import pandas as pd
import datetime

from Candle import BidAskCandle

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
               Including the:
               start: Time for first candle
               end: Time for last candle
               dailyAlignment: int
               instrument: AUD_USD
               granularity: 'D'
               alignmentTimezone: 'Europe/London'
        resp : object
               returned by requests module
        instrument: str
        '''

        startObj=self.validate_datetime(params['start'], params['granularity'])
        endObj = self.validate_datetime(params['end'], params['granularity'])

        #Increase end time by one minute to make the last candle end time match the params['end']
        min = datetime.timedelta(minutes=1)
        endI=params['end']
        endObj=endObj+min
        params['end']=endObj.isoformat()

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
                self.__validate_end(end=endI)

    def validate_datetime(self,datestr,granularity):
        '''

        Parameters
        ----------
        datestr : string
                  String representing a date
        granularity : string
                      Timeframe
        '''
        # Generate a datetime object from string
        dateObj = None
        try:
            dateObj = pd.datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            raise ValueError("Incorrect date format, should be %Y-%m-%dT%H:%M:%S")

        # check if datetime falls on close market
        if dateObj.weekday() == 4 and dateObj.time() >= time(22, 0, 0):
            raise Exception("Date {0} is not valid and falls on closed market".format(datestr))

        nhours=None
        if granularity == "D":
           nhours=24
        else:
            nhours = int(granularity.replace('H', ''))

        base= datetime.time(22, 00, 00)
        valid_time = [(datetime.datetime.combine(datetime.date(1, 1, 1), base) + datetime.timedelta(hours=x)).time() for x in range(0, 24, nhours)]

        if dateObj.time() not in valid_time:
            raise Exception("Time not valid. Valid times for {0} granularity are: {1}".format(granularity, valid_time))
        return dateObj


    def __validate_end(self,end):
        '''
        Private method to check that last candle time matches the 'end' time provided
        within params

        Parameters
        ---------
        end :   Datetime in isoformat

        Returns
        -------
        Nothing
        '''

        endO=pd.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S')
        endFetched=pd.datetime.strptime(self.data['candles'][-1]['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if endO != endFetched:
            raise Exception("Last candle time does not match the provided end time")

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

    def __repr__(self):
        return "BidAskCandle"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str
