import logging
import json
import pdb
import datetime

# create logger
s_logger = logging.getLogger(__name__)
s_logger.setLevel(logging.INFO)

class ser_data_obj(object):
    """
    Class to deal with candle serialized data

    Constructor

    Class variables
    ---------------
    ifile: str, Required
           File containing the serialized data (generated with oanda_api.serialize_data)
    data: dict
    """

    def __init__(self, ifile):
        self.ifile = ifile
        self.data = self.process_ifile()

    def slice(self, start, end=None, count=None):
        """
        Function to slice self.data to
        'start' and 'end'

        Parameters
        ----------
        start: datetime object, Requiree
        end: datetime object, Optional
        count: int, Optional
               Number of candles to retrieve

        Returns
        -------
        Dict with sliced data
        """
        new_candles = []
        ct = 0
        init = False
        for c in self.data['candles']:
            c_time = datetime.datetime.strptime(c['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
            if init is False and c_time > start:
                raise Exception("First fetched candle is after: {0}".format(start))
            else:
                init = True

            if end is not None:
                if c_time >= start and c_time <= end:
                    new_candles.append(c)
                elif c_time >= end:
                    break
            elif count is not None:
                if c_time >= start and ct < count:
                    ct += 1
                    new_candles.append(c)
                elif ct > count:
                    break

        new_dict = self.data
        del new_dict['candles']
        new_dict['candles'] = new_candles

        return new_dict

    def process_ifile(self):
        """
        Function to process file pointed by self.ifile

        Returns
        -------
        dict
        """
        inf = open(self.ifile, 'r')
        parsed_json = json.load(inf)
        inf.close()

        return parsed_json