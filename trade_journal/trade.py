from __future__ import division

import math
import warnings
from apis.oanda_api import OandaAPI
from candle.candlelist import CandleList
from harea.harea import HArea
from utils import *
from configparser import ConfigParser

class Trade(object):
    '''
    This class represents a single row from the dataframe in the trade_journal class

    Class variables
    ---------------

    entered: Boolean, Optional
             False if trade not taken (price did not cross self.entry). True otherwise
             Default : False
    trend_i: datetime, Optional
             start of the trend
    start: datetime, Required
           Time/date when the trade was taken. i.e. 20-03-2017 08:20:00s
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    outcome: str, Optional
             Outcome of the trade. Possible values are: success, failure, breakeven
    end: datetime, Optional
         Time/date when the trade ended. i.e. 20-03-2017 08:20:00
    entry: float, Optional
           entry price
    entry_time: datetime.optional
                Datetime for price reaching the entry price
    type: str, Optional
          What is the type of the trade (long,short)
    SL:  float, Optional
         Stop/Loss price
    TP:  float, Optional
         Take profit price. If not defined then it will calculated by using the RR
    SR:  float, Optional
         Support/Resistance area
    RR:  float, Optional
         Risk Ratio
    pips:  int, Optional
           Number of pips of profit/loss. This number will be negative if outcome was failure
    strat: string, Required
           What strategy was used for this trade.
    id : str, Required
         Id used for this object
    settingf : str, Optional
               Path to *.ini file with settings
    settings : ConfigParser object generated using 'settingf'
               Optional
    '''

    def __init__(self, strat, start, settingf=None, settings=None, entered=False, **kwargs):
        self.__dict__.update(kwargs)
        if not hasattr(self, 'TP') and not hasattr(self, 'RR'):
            raise Exception("Neither the RR not "
                            "the TP is defined. Please provide RR")
        elif not hasattr(self, 'TP') and math.isnan(self.RR):
            raise Exception("Neither the RR not "
                            "the TP is defined. Please provide RR")
        elif hasattr(self, 'RR') and not math.isnan(self.RR):
            diff = (self.entry - self.SL) * self.RR
            self.TP = round(self.entry + diff, 4)

        self.strat = strat
        self.start = datetime.strptime(start,
                                      '%Y-%m-%d %H:%M:%S')
        self.pair = re.sub('/', '_', self.pair)
        self.strat = strat
        #remove potential whitespaces in timeframe
        self.timeframe = re.sub(' ', '', self.timeframe)
        self.settingf = settingf
        self.settings = settings
        self.entered = entered

        # parse settings file (in .ini file)
        parser = ConfigParser()
        parser.read(settingf)
        self.settings = parser

    def fetch_candlelist(self):
        '''
        This function returns a CandleList object for this Trade

        Returns
        -------

        A CandleList object

        '''
        oanda = OandaAPI(instrument=self.pair,
                         granularity=self.timeframe,
                         settingf=self.settingf)

        if isinstance(self.start, datetime) is True:
            astart = self.start
        else:
            astart = try_parsing_date(self.start)

        if isinstance(self.end, datetime) is True:
            anend = self.end
        else:
            anend = try_parsing_date(self.end)

        oanda.run(start=astart.isoformat(),
                  end=anend.isoformat())

        candle_list = oanda.fetch_candleset()
        cl = CandleList(candle_list,
                        type=self.type,
                        settingf=self.settingf)

        return cl

    def run_trade(self, expires=None):
        '''
        Run the trade until conclusion from a start date
        '''

        print("[INFO] Run run_trade with id: {0}".format(self.id))
        entry = HArea(price=self.entry,
                      instrument=self.pair,
                      pips=self.settings.getint('trade', 'hr_pips'),
                      granularity=self.timeframe,
                      settings=self.settings)
        SL = HArea(price=self.SL,
                   instrument=self.pair,
                   pips=self.settings.getint('trade', 'hr_pips'),
                   granularity=self.timeframe,
                   settings=self.settings)
        TP = HArea(price=self.TP,
                   instrument=self.pair,
                   pips=self.settings.getint('trade', 'hr_pips'),
                   granularity=self.timeframe,
                   settings=self.settings)

        period = None
        if self.timeframe == "D":
            period = 24
        else:
            period = int(self.timeframe.replace('H', ''))

        # generate a range of dates starting at self.start and ending numperiods later in order to assess the outcome
        # of trade and also the entry time

        self.start = datetime.strptime(str(self.start), '%Y-%m-%d %H:%M:%S')
        numperiods = self.settings.getint('trade', 'numperiods')
        # date_list will contain a list with datetimes that will be used for running self
        date_list = [datetime.strptime(str(self.start.isoformat()), '%Y-%m-%dT%H:%M:%S')
                     + timedelta(hours=x*period) for x in range(0, numperiods)]

        count = 0
        self.entered = False

        for d in date_list:
            count += 1
            if expires is not None:
                if count > expires and self.entered is False:
                    self.outcome = 'n.a.'
                    break
            oanda = OandaAPI(instrument=self.pair,
                             granularity=self.timeframe,
                             settingf=self.settingf)

            oanda.run(start=d.isoformat(),
                      count=1)

            cl = oanda.fetch_candleset()[0]
            if self.entered is False:
                entry_time = entry.get_cross_time(candle=cl)
                if entry_time != 'n.a.':
                    print("\t[INFO] Trade entered")
                    self.entry_time = entry_time.isoformat()
                    self.entered = True
            if self.entered is True:
                failure_time = SL.get_cross_time(candle=cl)
                if failure_time is not None and failure_time != 'n.a.':
                    self.outcome = 'failure'
                    self.end = failure_time
                    self.pips = float(calculate_pips(self.pair,abs(self.SL-self.entry)))*-1
                    print("\t[INFO] S/L was hit")
                    break
                success_time = TP.get_cross_time(candle=cl)
                if success_time is not None and success_time !='n.a.':
                    self.outcome = 'success'
                    print("\t[INFO] T/P was hit")
                    self.end = success_time
                    self.pips = float(calculate_pips(self.pair,
                                                     abs(self.TP - self.entry)))
                    break
        try:
            assert getattr(self, 'outcome')
        except:
            warnings.warn("\tNo outcome could be calculated")
            self.outcome = "n.a."
            self.pips = 0

        print("\t[INFO] Done run_trade")

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()
