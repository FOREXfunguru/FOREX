from datetime import timedelta
from apis.oanda_api import OandaAPI
from configparser import ConfigParser

import logging
import pdb

# create logger
h_logger = logging.getLogger(__name__)
h_logger.setLevel(logging.INFO)

class HArea(object):
    '''
    Class to represent a horizontal area in the chart

    Class variables
    ---------------
    price : float, Required
            Price in the chart used as the middle point that will be extended on both sides a certain
            number of pips
    instrument : str, Required
                 Instrument for this CandleList (i.e. AUD_USD or EUR_USD etc...)
    granularity : str, Required
                Granularity for this CandleList (i.e. D, H12, H8 etc...)
    pips : int, Required
        Number of pips above/below self.price to calculate self.upper and self.lower
    upper : float, Optional
           Upper limit price of area
    lower : float, Optional
            Lower limit price of area
    no_pivots : int, Optional
                Number of pivots bouncing on self
    tot_score : int, Optional
                Total score, which is the sum of scores of all pivots
                on this HArea
    settingf : str, Optional
               Path to *.ini file with settings
    settings : ConfigParser, Optional
               ConfigParser object with settings
    ser_data_obj : ser_data_obj, Optional
                   ser_data_obj with serialized data
    '''

    def __init__(self, price, instrument, granularity, pips, no_pivots=None,
                 tot_score=None, settingf=None, settings=None, ser_data_obj=None):

        (first, second) = instrument.split("_")
        self.instrument = instrument
        round_number = None
        divisor = None
        if first == 'JPY' or second == 'JPY':
            round_number = 2
            divisor = 100
        else:
            round_number = 4
            divisor = 10000
        price = round(price, round_number)
        self.price = price
        self.granularity = granularity
        self.no_pivots = no_pivots
        self.tot_score = tot_score
        self.settingf = settingf
        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

        self.ser_data_obj = ser_data_obj
        self.upper = round(price+(pips/divisor), 4)
        self.lower = round(price-(pips/divisor), 4)

    def last_time(self, clist, position):
        '''
        Function that returns the datetime of the moment where prices were over/below this HArea.

        Parameters
        ----------
        clist   list
                List with Candles
        position    This parameter controls if price should cross the HArea.upper for 'above'
                    or HArea.lower for 'below'
                    Possible values are: 'above' or 'below'

        Return
        ------
        datetime object of the moment that the price crosses the HArea
        '''
        count = 0

        for c in reversed(clist):
            count += 1
            # Last time has to be at least self.settings.getint('harea', 'min') candles before
            if count <= self.settings.getint('harea', 'min'):
                continue
            if position == 'above':
                price = getattr(c, 'lowAsk')
                if price > self.upper:
                    return c.time
            elif position == 'below':
                price = getattr(c, 'highAsk')
                if price < self.lower:
                    return c.time

    def get_cross_time(self, candle, granularity='M30'):
        '''
        This function is used get the time that the candle
        crosses (go through) HArea

        Parameters
        ----------
        candle :   Candle object that crosses the HArea
        granularity : To what granularity we should descend

        Returns
        ------
        datetime object with crossing time.
                 n.a. if crossing time could not retrieved. This can happens
                 when there is an artefactual jump in Oanda's data
        '''
        if candle.lowAsk <= self.price <= candle.highAsk:

            delta = None
            if self.granularity == "D":
                delta = timedelta(hours=24)
            else:
                fgran = self.granularity.replace('H', '')
                delta = timedelta(hours=int(fgran))

            cstart = candle.time
            cend = cstart+delta

            oanda = None
            if self.settingf is None and self.settings is None:
                raise Exception("No 'settings' nor 'settingf' defined for this object")
            elif self.settingf is None and self.settings is not None:
                oanda = OandaAPI(instrument=self.instrument,
                                 granularity=granularity,  # 'M30' in this case
                                 settings=self.settings)
            elif self.settingf is not None and self.settings is None:
                oanda = OandaAPI(instrument=self.instrument,
                                 granularity=granularity,  # 'M30' in this case
                                 settingf=self.settingf)
            elif self.settingf is not None and self.settings is not None:
                oanda = OandaAPI(instrument=self.instrument,
                                 granularity=granularity,  # 'M30' in this case
                                 settingf=self.settingf)

            if self.ser_data_obj is None:
                h_logger.debug("Fetching data from API")
                oanda.run(start=cstart.isoformat(),
                          end=cend.isoformat())
            else:
                h_logger.debug("Fetching data from File")
                oanda.data = self.ser_data_obj.slice(start=cstart,
                                                     end=cend)

            candle_list = oanda.fetch_candleset()
            seen = False
            for c in candle_list:
                if c.lowAsk <= self.price <= c.highAsk:
                    seen = True
                    return c.time

            if seen is False:
                return 'n.a.'
        else:
            return 'n.a.'

    def __repr__(self):
        return "HArea"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str