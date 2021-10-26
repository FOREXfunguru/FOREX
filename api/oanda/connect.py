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
import pandas as pd
from config import CONFIG
from typing import Dict, List, Any
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

    def _parse_ser_data_c(self, indir : str, params)->Dict[str, Any]:
        """Function to parse the serialized JSON file
        with FOREX data and will execute the desired query with
        a 'start' and 'count' params."""

        start = datetime.datetime.strptime(params['start'], '%Y-%m-%dT%H:%M:%S')
        year_start = start.year
        new_candles = []
        delta1hr = datetime.timedelta(hours=1)
        ct = 0
        inyear = False
        for year in range(2007, 2021):
            if year < year_start:
                continue
            if inyear is True:
                year_start = year
            infile = "{0}/{1}.{2}.{3}.ser".format(indir, self.instrument,
                                                      self.granularity, year)
            inf = open(infile, 'r')
            parsed_json = json.load(inf)
            inf.close()
            if year == year_start:
                inyear = True
                for c in parsed_json['candles']:
                    if ct == params['count']:
                        break
                    c_time = datetime.datetime.strptime(c['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    if self.granularity == 'H1':
                        if (c_time >= start):
                            new_candles.append(c)
                            ct = ct + 1
                    else:
                        if ((c_time >= start) or (abs(c_time - start) <= delta1hr)):
                            new_candles.append(c)
                            ct = ct+1

        return {'granularity': self.granularity,
                'instrument' : self.instrument,
                'candles' : new_candles}

    def _parse_ser_data_s_e(self, indir : str, params : Dict[str, Any])-> List:
        """Private function that will parse the serialized JSON file
        with FOREX data and will execute the desired query with
        a 'start' and 'end' params.

        Args:
            indir : path to dir containing the serialized data
            params : Params of the query. i.e. start, end, count ...

        Returns
        -------
        List of dicts. Each dict contains data for a candle
        """
        start = datetime.datetime.strptime(params['start'], '%Y-%m-%dT%H:%M:%S')
        end = datetime.datetime.strptime(params['end'], '%Y-%m-%dT%H:%M:%S')
        year_start = start.year
        year_end = end.year

        new_candles = []
        delta1hr = datetime.timedelta(hours=1)
        for year in range(2007, 2021+1):
            if year < year_start:
                continue
            elif year > year_end:
                break

            infile = "{0}/{1}.{2}.{3}.ser".format(indir, self.instrument,
                                                  self.granularity, year)
            inf = open(infile, 'r')
            parsed_json = json.load(inf)
            inf.close()
            if year == year_start or year == year_end:
                for c in parsed_json['candles']:
                    c_time = datetime.datetime.strptime(c['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    if ((c_time >= start) or (abs(c_time - start) <= delta1hr)) and ((c_time <= end) or (abs(c_time - end) <= delta1hr)):
                        new_candles.append(c)
                    elif (c_time >= end) and (abs(c_time - end) > delta1hr):
                        break
            else:
                new_candles = new_candles + parsed_json['candles']

        return {'granularity': self.granularity,
                'instrument' : self.instrument,
                'candles' : new_candles}

    def mquery(self, start : datetime, end : datetime, outfile : str =None)->List[Dict]:
        """Function to execute a batch query on the Oanda API
        This is necessary when for example, the query hits
        the max number of returned candles for the Oanda API

        Args:
            start: isoformat
            end: isoformat
            outfile: File to write the serialized data returned
        """

        startO = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
        endO = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S')
        patt = re.compile(r"\dD")
        delta = nhours = None
        if patt.match(self.granularity):
            raise Exception("{0} is not valid. Oanda REST service does not accept it".format(granularity))
        elif self.granularity == "D":
            nhours = 24
            delta = datetime.timedelta(hours=24)
        else:
            p1 = re.compile('^H')
            m1 = p1.match(self.granularity)
            if m1:
                nhours = int(self.granularity.replace('H', ''))
                delta = datetime.timedelta(hours=int(nhours))
            p2 = re.compile('^M')
            m2 = p2.match(self.granularity)
            if m2:
                nmins = int(self.granularity.replace('M', ''))
                delta = datetime.timedelta(minutes=int(nmins))

        # 5000 candles is the Oanda's limit
        res = None
        while startO <= endO:
            if res is None:
                res = self.query(startO.isoformat(), count=5000)
            else:
                res_l = self.query(startO.isoformat(), count=5000)
                res['candles'] = res['candles'] + res_l['candles']
            startO = datetime.datetime.strptime(res['candles'][-1]['time'][:-4],
                                                '%Y-%m-%dT%H:%M:%S.%f')
            if startO > endO:
                new_list = []
                for c in res['candles']:
                    adtime = datetime.datetime.strptime(c['time'][:-4],
                                                        '%Y-%m-%dT%H:%M:%S.%f')
                    if adtime <= endO:
                        new_list.append(c)
                res['candles'] = new_list

            startO = startO + delta

        if outfile is not None:
            ser_data = json.dumps(res)
            f = open(outfile, "w")
            f.write(ser_data)
            f.close()

        return res

    @retry()
    def query(self, start : datetime, end : datetime = None, count : int = None,
              indir : str = None, outfile : str = None)-> list[Dict]:
        """Function 'query' overloads and will behave differently
        depending on the presence/absence of the following args:

        'indir': If this arg is present, then the query of FOREX
        data will be done on the serialized data in the JSON format.
        'outfile': If this arg is present, then the function will
        query the REST API and will serialized the data into a JSON
        file.
        Finally, if neither 'indir' nor 'outfile' are present, then
        the function will do a REST API query and nothing else

        Args:
            start: isoformat
            end:   isoformat
            count: If end is not defined, this controls the
                   number of candles from the start
                   that will be retrieved
            indir: path to DIR containing the JSON files with serialized FOREX data
            outfile: File to write the serialized data returned
                     by the API.

        Returns:
            Each dict contains data for a candle"""
        startObj = None
        if indir is not None:
            # do not validate if there is serialized data
            startObj = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
        else:
            startObj = self.validate_datetime(start, self.granularity)
        start = startObj.isoformat()
        params = {}
        if end is not None and count is None:
            endObj = None
            if indir is not None:
                # do not validate if there is serialized data
                endObj = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S')
            else:
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
        if indir is not None:
            o_logger.debug("Serialized data provided. Candles will be "
                          "fetched from files in dir {0}".format(indir))
            if 'end' in params:
                return self._parse_ser_data_s_e(indir, params)
            elif 'count' in params:
                return self._parse_ser_data_c(indir, params)
        else:
            resp = None
            try:
                resp = requests.get(url=f"{CONFIG.get('oanda_api', 'url')}/{self.instrument}/candles",
                                    params=params,
                                    headers={"content-type": f"{CONFIG.get('oanda_api', 'content_type')}",
                                             "Authorization": f"{os.environ.get('TOKEN')}"})
                if resp.status_code != 200:
                    raise Exception(resp.status_code)
                else:
                    data = json.loads(resp.content.decode("utf-8"))
                    if outfile is not None:
                        ser_data = json.dumps(data)
                        f = open(outfile, "w")
                        f.write(ser_data)
                        f.close()
                    return data
            except Exception as err:
                # Something went wrong.
                print("Something went wrong. url used was:\n{0}".format(resp.url))
                print("Error message was: {0}".format(err))
                return resp.status_code

    def validate_datetime(self, datestr : str, granularity: str):
        """Function to parse a string datetime to return
         a datetime object and to validate the datetime.

        Args:
            datestr : String representing a date
            granularity : Timeframe
        """
        # Generate a datetime object from string
        dateObj = None
        try:
            dateObj = datetime.datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            raise ValueError("Incorrect date format, should be %Y-%m-%dT%H:%M:%S")

        patt = re.compile(r"\dD")
        nhours = delta = None
        if patt.match(granularity):
            raise Exception("{0} is not valid. Oanda REST service does not accept it".format(granularity))
        elif granularity == "D":
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
        endObj = dateObj+delta

        # check if datestr returns a candle
        params = {}
        params['instrument'] = self.instrument
        params['granularity'] = self.granularity
        params['start'] = datestr
        params['end'] = endObj.isoformat()
        resp = requests.get(url=CONFIG.get('oanda_api', 'url'),
                            params=params)
        # 204 code means 'no_content'
        if resp.status_code == 204:
            if CONFIG.getboolean('oanda_api', 'roll') is True:
                dateObj = self.__roll_datetime(dateObj, granularity)
            else:
                raise Exception("Date {0} is not valid and falls on closed market".format(datestr))

        if nhours is not None:
            base= datetime.time(22, 00, 00)
            # generate a list with valid times. For example, if granularity is H12, then it will be 22 and 10
            valid_time = [(datetime.datetime.combine(datetime.date(1, 1, 1), base) +
                           datetime.timedelta(hours=x)).time() for x in range(0, 24, nhours)]

            # daylightime saving discrepancy
            base1 = datetime.time(21, 00, 00)
            valid_time1 = [(datetime.datetime.combine(datetime.date(1, 1, 1), base1) +
                            datetime.timedelta(hours=x)).time() for x in range(0, 24, nhours)]
        return dateObj

    def _roll_datetime(self, dateObj : datetime, granularity : str)->datetime:
        """Private function to roll the datetime, which falls on a closed market to the next period (set by granularity)
        with open market.

        If dateObj falls before the start of the historical data record for self.instrument then roll to the start
        of the historical record

        Args:
            dateObj
            granularity : D, H12 and so on

        Returns:
            rolled datetime object
        """
        # check if dateObj is previous to the start of historical data for self.instrument
        if not CONFIG.has_option('pairs_start', self.instrument):
            raise Exception("Inexistent start of historical record info for {0}".format(self.instrument))

        start_hist_dtObj = self.try_parsing_date(CONFIG.get('pairs_start', self.instrument))
        if dateObj < start_hist_dtObj:
            rolledateObj = start_hist_dtObj
            o_logger.debug("Date precedes the start of the historical record.\n"
                           "Time was rolled from {0} to {1}".format(dateObj, rolledateObj))
            return rolledateObj

        delta = None
        if granularity == "D":
            delta = datetime.timedelta(hours=24)
        else:
            p1 = re.compile('^H')
            m1 = p1.match(granularity)
            if m1:
                nhours = int(granularity.replace('H', ''))
                delta = datetime.timedelta(hours=int(nhours))
            p2 = re.compile('^M')
            m2 = p2.match(granularity)
            if m2:
                nmins = int(granularity.replace('M', ''))
                delta = datetime.timedelta(minutes=int(nmins))

        resp_code = 204
        startObj = dateObj
        while resp_code == 204:
            startObj = startObj+delta
            endObj = startObj+delta
            #check if datestr returns a candle
            params = {}
            params['instrument'] = self.instrument
            params['granularity'] = self.granularity
            params['start'] = dateObj.isoformat()
            params['end'] = endObj.isoformat()

            resp = requests.get(url=CONFIG.get('oanda_api', 'url'),
                                params=params)
            resp_code = resp.status_code
        o_logger.debug("Time was rolled from {0} to {1}".format(dateObj, startObj))
        return startObj

    def _validate_end(self, endObj : datetime)->int:
        """Private method to check that last candle time matches the 'end' time provided
        within params.

        Args:
            endObj

        Returns:
            1 if it validates
        """
        endFetched = datetime.datetime.strptime(self.data['candles'][-1]['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if endObj != endFetched:
            #check if discrepancy is not in the daylight savings period
            fetched_time = endFetched.time()
            passed_time = endObj.time()
            dateTimefetched = datetime.datetime.combine(datetime.date.today(), fetched_time)
            dateTimepassed = datetime.datetime.combine(datetime.date.today(), passed_time)
            dateTimeDifference = dateTimefetched - dateTimepassed
            dateTimeDifferenceInHours = dateTimeDifference.total_seconds() / 3600
            if endFetched.date() == endObj.date() and abs(dateTimeDifferenceInHours) <= 1:
                return 1
            else:
                raise Exception("Last candle time does not match the provided end time")
        else:
            return 1

    def print_url(self)->str:
        """Print url from requests module"""
        
        print("URL: %s" % self.resp.url)

    def try_parsing_date(self, text):
        '''
        Function to parse a string that can be formatted in
        different datetime formats

        :returns
        datetime object
        '''

        for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
            try:
                return datetime.datetime.strptime(text, fmt)
            except ValueError:
                pass
        raise ValueError('no valid date format found')

    def __repr__(self)->str:
        return "connect"

    def __str__(self)->str:
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str
