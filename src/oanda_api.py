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
import config
import time

from candle import BidAskCandle

class OandaAPI(object):
    '''
    Class representing the content returned by a GET request to Oanda's REST API
    '''

    def __init__(self, instrument, granularity, url=None, data=None, **kwargs):
        '''
        Constructor

         Class variables
        ---------------
        instrument: AUD_USD. Required
        granularity: 'D'. Required
        url : string
              Oanda's REST service url
        data : object
               Deserialized content returned by requests' 'get'
        dailyAlignment: int
        alignmentTimezone: 'Europe/London'
        '''

        self.instrument=instrument
        self.granularity=granularity
        self.url=url
        self.data=data

        allowed_keys = ['dailyAlignment','granularity',
                        'alignmentTimezone']
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)

    def retry(cooloff=5, exc_type=None):
        '''
        Decorator for retrying connection and prevent TimeOut errors
        '''
        if not exc_type:
            exc_type = [requests.exceptions.ConnectionError]

        def real_decorator(function):
            def wrapper(*args, **kwargs):
                while True:
                    try:
                        return function(*args, **kwargs)
                    except Exception as e:
                        if e.__class__ in exc_type:
                            print("failed (?)")
                            time.sleep(cooloff)
                        else:
                            raise e

            return wrapper

        return real_decorator

    @retry()
    def run(self, start, end=None, count=None,roll=False):
        '''
        Function to run a particular REST query. It will set self.data with the data response

        Parameters
        ----------

        start: Datetime object
               Date and time for first candle. Required
        end:   Datetime object
               Date and time for last candle. Optional
        count: int
               If end is not defined, then this controls the number of candles from the start
               that will be retrieved
        roll: bool
               If True, then extend the end date, which falls on close market, to the next period for which
               the market is open. Default=False

        Returns
        -------
        int: Response code of the REST query
        '''

        startObj = self.validate_datetime(start, self.granularity, roll=roll)
        start = startObj.isoformat()
        params={}
        params['instrument'] = self.instrument
        params['granularity'] = self.granularity
        params['start'] = start
        endObj = None
        if end is not None and count is None:
            endObj = self.validate_datetime(end, self.granularity, roll=roll)

            # Increase end time by one minute to make the last candle end time match the params['end']
            min = datetime.timedelta(minutes=1)
            endObj = endObj + min
            end = endObj.isoformat()
            params['end']=end
        elif count is not None:
            params['count'] = count
        elif end is None and count is None:
            raise Exception("You need to set at least the 'end' or the 'count' attribute")

        if self.url:

            resp = requests.get(url=self.url, params=params)

            if resp.status_code != 200:
                # This means something went wrong.
                print("Something went wrong. url used was:\n{0}".format(resp.url))
                raise Exception('GET /candles {}'.format(resp.status_code))

            self.data = json.loads(resp.content.decode("utf-8"))
           # if 'end' in params: self.__validate_end(endObj - min)

    def validate_datetime(self,datestr,granularity,roll=False):
        '''
        Function to parse a string datetime to return a datetime object and to validate the datetime

        Parameters
        ----------
        datestr : string
                  String representing a date
        granularity : string
                      Timeframe
        roll : bool
               If True, then extend the end date, which falls on close market, to the next period for which
               the market is open. Default=False
        '''

        # Generate a datetime object from string
        dateObj = None
        try:
            dateObj = pd.datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            raise ValueError("Incorrect date format, should be %Y-%m-%dT%H:%M:%S")

        nhours=None
        delta = None
        if granularity == "D":
            nhours=24
            delta = datetime.timedelta(hours=24)
        else:
            p1 = re.compile('^H')
            m1 = p1.match(granularity)
            if m1:
                nhours = int(granularity.replace('H', ''))
                delta = datetime.timedelta(hours=int(nhours))
            nmins = None
            p2 = re.compile('^M')
            m2 = p2.match(granularity)
            if m2:
                nmins = int(granularity.replace('M', ''))
                delta = datetime.timedelta(minutes=int(nmins))

        # increment dateObj by one period. This is necessary in order to query Oanda
        endObj=dateObj+delta

        #check if datestr returns a candle
        params = {}
        params['instrument'] = self.instrument
        params['granularity'] = self.granularity
        params['start'] = datestr
        params['end'] = endObj.isoformat()

        resp = requests.get(url=self.url, params=params)
        # 204 code means 'no_content'
        if resp.status_code==204:
            if roll is True:
                dateObj=self.__roll_datetime(dateObj,granularity)
            else:
                raise Exception("Date {0} is not valid and falls on closed market".format(datestr))

        if nhours is not None:
            base= datetime.time(22, 00, 00)
            valid_time = [(datetime.datetime.combine(datetime.date(1, 1, 1), base) + datetime.timedelta(hours=x)).time() for x in range(0, 24, nhours)]

            # daylightime saving discrepancy
            base1 = datetime.time(21, 00, 00)
            valid_time1 = [(datetime.datetime.combine(datetime.date(1, 1, 1), base1) + datetime.timedelta(hours=x)).time() for x in range(0, 24, nhours)]
            if (dateObj.time() not in valid_time) and (dateObj.time() not in valid_time1):
                raise Exception("Time {0} not valid. Valid times for {1} granularity are: {2} or are: {3}".format(dateObj.time(),
                                                                                                                  granularity, valid_time,
                                                                                                                  valid_time1))
        return dateObj


    def __roll_datetime(self,dateObj,granularity):
        '''
        Private function to roll the datetime, which falls on a closed market to the next period (set by granularity)
        with open market

        If dateObj falls before the start of the historical data record for self.instrument then roll to the start
        of the historical record

        Parameters
        ----------
        dateObj : datetime object

        Returns
        -------
        datetime object
                 Returns the rolled datetime object
        '''

        # check if dateObj is previous to the start of historical data for self.instrument
        if self.instrument not in config.START_HIST:
            raise Exception("Inexistent start of historical record info for {0}".format(self.instrument))

        if dateObj < config.START_HIST[self.instrument]:
            rolledateObj= config.START_HIST[self.instrument]
            print("Date precedes the start of the historical record.\n"
                  "Time was rolled from {0} to {1}".format(dateObj, rolledateObj))
            return rolledateObj

        delta = None
        if granularity == "D":
            delta = datetime.timedelta(hours=24)
        else:
            nhours=None
            p1 = re.compile('^H')
            m1 = p1.match(granularity)
            if m1:
                nhours = int(granularity.replace('H', ''))
                delta = datetime.timedelta(hours=int(nhours))
            nmins = None
            p2 = re.compile('^M')
            m2 = p2.match(granularity)
            if m2:
                nmins = int(granularity.replace('M', ''))
                delta = datetime.timedelta(minutes=int(nmins))

        resp_code=204
        startObj=dateObj
        endObj=None
        while resp_code==204:
            startObj=startObj+delta
            endObj=startObj+delta
            #check if datestr returns a candle
            params = {}
            params['instrument'] = self.instrument
            params['granularity'] = self.granularity
            params['start'] = dateObj.isoformat()
            params['end'] = endObj.isoformat()

            resp = requests.get(url=self.url, params=params)
            resp_code=resp.status_code

        print("Time was rolled from {0} to {1}".format(dateObj,startObj))
        return startObj

    def __validate_end(self,endObj):
        '''
        Private method to check that last candle time matches the 'end' time provided
        within params

        Parameters
        ---------
        endObj :   Datetime object

        Returns
        -------
        1 if it validates
        '''

        endFetched=pd.datetime.strptime(self.data['candles'][-1]['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if endObj!= endFetched:
            #check if discrepancy is not in the daylight savings period
            fetched_time=endFetched.time()
            passed_time=endObj.time()
            dateTimefetched = datetime.datetime.combine(datetime.date.today(), fetched_time)
            dateTimepassed = datetime.datetime.combine(datetime.date.today(), passed_time)
            dateTimeDifference = dateTimefetched - dateTimepassed
            dateTimeDifferenceInHours = dateTimeDifference.total_seconds() / 3600
            if endFetched.date()==endObj.date() and abs(dateTimeDifferenceInHours)<=1:
                return 1
            else:
                raise Exception("Last candle time does not match the provided end time")
        else:
            return 1


    def print_url(self):
        '''
        Print url from requests module
        '''
        
        print("URL: %s" % self.resp.url)
        
    def fetch_candleset(self, vol_cutoff=0):
        '''
        Retrieve candles in self.data


        Parameters
        ----------
        vol_cutoff: int
                    Do not consider candles having less than 'vol_cutoff'.
                    Default: 0
        
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
                if cd.volume > vol_cutoff: candlelist.append(cd)
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
