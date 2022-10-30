'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
import datetime
import time
import logging
import requests
import re
import pdb
import os
import datetime
import json
import sys
import flatdict
import argparse

from api.params import Params as apiparams
from typing import Dict, List
from forex.candle import CandleList
import time

# create logger
o_logger = logging.getLogger(__name__)
o_logger.setLevel(logging.INFO)

class Connect(object):
    """Class representing a connection to the Oanda's REST API.

    Args:
        instrument: i.e. AUD_USD
        granularity: i.e. D, H12, ...
    """
    def __init__(self, instrument: str, granularity: str)->None:
        self._instrument = instrument
        self._granularity = granularity

    @property
    def instrument(self)->str:
        return self._instrument

    @property
    def granularity(self)->str:
        return self._granularity

    def retry(cooloff: int=5, exc_type=None):
        """Decorator for retrying connection and prevent TimeOut errors"""
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
    def query(self, start : datetime, end : datetime = None, count : int = None)-> List[Dict]:
        """Function to query Oanda's REST API

        Args:
            start: isoformat
            end:   isoformat
            count: If end is not defined, this controls the
                   number of candles from the start
                   that will be retrieved
        Returns:
            CandleList"""
        startObj = self.validate_datetime(start, self.granularity)
        start = startObj.isoformat()
        params = {}
        if end is not None and count is None:
            endObj = self.validate_datetime(end, self.granularity)
            min = datetime.timedelta(minutes=1)
            endObj = endObj + min
            end = endObj.isoformat()
            params['to'] = end
        elif count is not None:
            params['count'] = count
        elif end is None and count is None:
            raise Exception("You need to set at least the 'end' or the "
                            "'count' attribute")

        params['granularity'] = self.granularity
        params['from'] = start
        try:
            resp = requests.get(url=f"{apiparams.url}/{self.instrument}/candles",
                                params=params,
                                headers={"content-type": f"{apiparams.content_type}",
                                         "Authorization": f"Bearer {os.environ.get('TOKEN')}"})
            if resp.status_code != 200:
                raise Exception(resp.status_code)
            else:
                data = json.loads(resp.content.decode("utf-8"))
                newdata = [flatdict.FlatDict(c, delimiter='.') for c in data['candles']]
                newdata1 = []
                for candle in newdata:
                    atime = re.sub(r'\.\d+Z$','', candle['time'])
                    candle['time']=atime
                    newdata1.append(candle)
                for mydict in newdata1:
                    mydict['h'] = mydict.pop('mid.h')
                    mydict['l'] = mydict.pop('mid.l')
                    mydict['o'] = mydict.pop('mid.o')
                    mydict['c'] = mydict.pop('mid.c')
                cl = CandleList(instrument=self.instrument,
                                granularity=self.granularity,
                                data=newdata1)
                return cl
        except Exception as err:
            # Something went wrong.
            print("Something went wrong. url used was:\n{0}".format(resp.url))
            print("Error message was: {0}".format(err))
            sys.exit(1)

    def validate_datetime(self, datestr : str, granularity: str)->datetime:
        """Function to parse a string datetime to return
         a datetime object and to validate the datetime.

        Args:
            datestr : String representing a date
            granularity : Timeframe
        """
        try:
            dateObj = datetime.datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            raise ValueError("Incorrect date format, should be %Y-%m-%dT%H:%M:%S")

        return dateObj

    def print_url(self)->str:
        """Print url from requests module"""
        
        print("URL: %s" % self.resp.url)

    def __repr__(self)->str:
        return "connect"

    def __str__(self)->str:
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Query Oanda REST API and generates a CandleList object and save it to a file')
 
    parser.add_argument('--start', required=True, help='Start datetime. i.e.:2018-05-21T21:00:00' )
    parser.add_argument('--end', required=True, help='End datetime. i.e.: 2018-05-23T21:00:00' )
    parser.add_argument('--instrument', required=True, help='AUD_USD, GBP_USD, ...' )
    parser.add_argument('--granularity', required=True, help='i.e. D,H12,H8, ...' )
    parser.add_argument('--outfile', required=True, help='Output filename')

    args = parser.parse_args()
    
    conn = Connect(
        instrument=args.instrument,
        granularity=args.granularity)

    clO = conn.query(start=args.start,
                     end=args.end)

    clO.pickle_dump(args.outfile)

    