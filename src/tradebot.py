from oanda_api import OandaAPI
from configparser import ConfigParser

class TradeBot(object):
    '''
    This class represents an automatic Trading bot

    Class variables
    ---------------
    start: datetime, Required
           Datetime that this Bot will start operating. i.e. 20-03-2017 08:20:00s
    end: datetime, Required
         Datetime that this Bot will end operating. i.e. 20-03-2020 08:20:00s
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    settingf : str, Optional
               Path to *.ini file with settings
    '''
    def __init__(self, start, end, pair, timeframe, settingf, settings=None):
        self.start = start
        self.end = end
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


    def run(self):
        oanda = OandaAPI(instrument=self.pair,
                         granularity=self.timeframe,
                         settingf=self.settingf)

        oanda.run(start=self.start,
                  count=1)

        candle_list = oanda.fetch_candleset()
