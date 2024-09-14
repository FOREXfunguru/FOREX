"""
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
"""
import datetime
import time
import logging
import requests
import re
import os
import json
import flatdict
import argparse
from datetime import timedelta

from api.params import Params as apiparams
from typing import Dict, List
from forex.candle import CandleList

o_logger = logging.getLogger(__name__)
o_logger.setLevel(logging.INFO)


class Connect(object):
    """Class representing a connection to the Oanda's REST API.

    Args:
        instrument: i.e. AUD_USD
        granularity: i.e. D, H12, ...
    """

    def __init__(self, instrument: str, granularity: str) -> None:
        self._instrument = instrument
        self._granularity = granularity

    @property
    def instrument(self) -> str:
        return self._instrument

    @property
    def granularity(self) -> str:
        return self._granularity

    def fetch_candle(self, d: datetime) -> "Candle":
        """Method to get a single candle"""
        # substract one min to be sure we fetch the right candle
        start = d - timedelta(minutes=1)
        clO = self.query(start=start.isoformat(), end=start.isoformat())
        hour_delta = timedelta(hours=1)
        
        if len(clO) == 0:
            #  try with hour-1 to deal with time shifts
            new_d = None
            if d.hour%2 > 0:
                new_d = d+hour_delta
            else:
                new_d = d-hour_delta
            clO = self.query(start=new_d.isoformat(), end=new_d.isoformat())

        if len(clO.candles) == 1:
            if (clO.candles[0].time != d) and abs(clO.candles[0].time - d) > hour_delta:
                # return None if candle is not equal to 'd'
                return
            return clO.candles[0]
        if len(clO.candles) > 1:
            raise Exception("No valid number of candles in CandleList")
        return

    def retry(cooloff: int = 5, exc_type=None):
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

    def _process_data(self, data: List[flatdict.FlatDict], strip: bool = True):
        """Process candle data

        Args:
            data: data returned by API
            strip: If True then remove 'complete' and 'volume' fields
        """
        keys_to_remove = ["complete", "volume", "time"]
        cldict = list()
        for candle in data:
            atime = re.sub(r"\.\d+Z$", "", candle["time"])
            if strip:
                candle = {
                    key: value
                    for key, value in candle.items()
                    if key not in keys_to_remove
                }
            candle["time"] = atime
            newc = {key.replace("mid.", ""): value for key, value in candle.items()}
            cldict.append(newc)
        return cldict

    @retry()
    def query(
        self, start: datetime, end: datetime = None, count: int = None
    ) -> List[Dict]:
        """Function to query Oanda's REST API

        Args:
            start: isoformat
            end:   isoformat
            count: If end is not defined, this controls the
                   number of candles from the start
                   that will be retrieved
        Returns:
            CandleList"""
        startObj = self.validate_datetime(start)
        start = startObj.isoformat()
        params = {}
        if end is not None and count is None:
            endObj = self.validate_datetime(end)
            min = datetime.timedelta(minutes=1)
            endObj = endObj + min
            end = endObj.isoformat()
            params["to"] = end
        elif count is not None:
            params["count"] = count
        elif end is None and count is None:
            raise Exception(
                "You need to set at least the 'end' or the " "'count' attribute"
            )

        params["granularity"] = self.granularity
        params["from"] = start
        try:
            resp = requests.get(
                url=f"{apiparams.url}/{self.instrument}/candles",
                params=params,
                headers={
                    "content-type": f"{apiparams.content_type}",
                    "Authorization": f"Bearer {os.environ.get('TOKEN')}",
                },
            )
            if resp.status_code != 200:
                raise ConnectionError(resp.status_code)
            else:
                data = json.loads(resp.content.decode("utf-8"))
                newdata = [flatdict.FlatDict(c, delimiter=".") for c in data["candles"]]
                newdata1 = self._process_data(data=newdata)
                return CandleList(
                    instrument=self.instrument,
                    granularity=self.granularity,
                    data=newdata1,
                )
        except ConnectionError as err:
            logging.exception(
                "Something went wrong. url used was:\n{0}".format(resp.url)
            )
            logging.exception("Error message was: {0}".format(err))
            return CandleList(
                instrument=self.instrument, granularity=self.granularity, data=[]
            )

    def validate_datetime(self, datestr: str) -> datetime:
        """Function to parse a string datetime to return
         a datetime object and to validate the datetime.

        Args:
            datestr : String representing a date
        """
        try:
            dateObj = datetime.datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            raise ValueError("Incorrect date format, should be %Y-%m-%dT%H:%M:%S")

        return dateObj

    def print_url(self) -> str:
        """Print url from requests module"""

        print("URL: %s" % self.resp.url)

    def __repr__(self) -> str:
        return "connect"

    def __str__(self) -> str:
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query Oanda REST API and generates a CandleList object and save it to a file"
    )

    parser.add_argument(
        "--start", required=True, help="Start datetime. i.e.:2018-05-21T21:00:00"
    )
    parser.add_argument(
        "--end", required=True, help="End datetime. i.e.: 2018-05-23T21:00:00"
    )
    parser.add_argument("--instrument", required=True, help="AUD_USD, GBP_USD, ...")
    parser.add_argument("--granularity", required=True, help="i.e. D,H12,H8, ...")
    parser.add_argument("--outfile", required=True, help="Output filename")

    args = parser.parse_args()

    conn = Connect(instrument=args.instrument, granularity=args.granularity)

    clO = conn.query(start=args.start, end=args.end)

    clO.pickle_dump(args.outfile)
