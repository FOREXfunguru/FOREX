from oanda_api import OandaAPI
from configparser import ConfigParser
import pdb
import pandas as pd
import datetime
import re

class TradeBot(object):
    '''
    This class represents an automatic Trading bot

    Class variables
    ---------------
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    settingf : str, Optional
               Path to *.ini file with settings
    '''
    def __init__(self, pair, timeframe, settingf, settings=None):
        self.pair = pair
        self.timeframe = timeframe
        self.settingf = settingf
        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings


    def run(self, start, end):
        '''
        This function will run the Bot from start to end
        one candle at a time

        Parameters
        ----------
        start: datetime, Required
            Datetime that this Bot will start operating. i.e. 20-03-2017 08:20:00s
        end: datetime, Required
            Datetime that this Bot will end operating. i.e. 20-03-2020 08:20:00s
        '''
        oanda = OandaAPI(instrument=self.pair,
                         granularity=self.timeframe,
                         settingf=self.settingf)
        delta = None
        nhours = None
        if self.timeframe == "D":
            nhours = 24
            delta = datetime.timedelta(hours=24)
        else:
            p1 = re.compile('^H')
            m1 = p1.match(self.timeframe)
            if m1:
                nhours = int(self.timeframe.replace('H', ''))
                delta = datetime.timedelta(hours=int(nhours))

        startO = pd.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
        endO = pd.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S')

        while startO <= endO:
            oanda.run(start=startO.isoformat(),
                      count=1)

            candle_list = oanda.fetch_candleset()
            startO = startO+delta

        print("h\n")
    def calc_SR(self):
        '''
        Function to calculate S/R lines
        :return:
        '''

        ul, ll = self.settings.get('tradebot', self.pair).split(",")