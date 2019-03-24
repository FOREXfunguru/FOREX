'''
Created on 24 Nov 2016

@author: ernesto lowy
'''

import pdb
import re
import os
import requests,json
import pandas as pd

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
