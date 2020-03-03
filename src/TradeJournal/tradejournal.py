import pandas as pd
import pdb
import math
import warnings
from TradeJournal.trade import Trade
from TradeJournal.tradelist import TradeList
from openpyxl import load_workbook
from configparser import ConfigParser
from pivotlist import PivotList

class TradeJournal(object):
    '''
    Constructor

    Class variables
    ---------------
    url: path to the .xlsx file with the trade journal
    worksheet: str, Required
               Name of the worksheet that will be used to create the object.
               i.e. trading_journal
    settingf : str, Required
               Path to *.ini file with settings
    '''

    def __init__(self, url, worksheet, settingf):
        self.url = url
        self.worksheet = worksheet
        #read-in the 'trading_journal' worksheet from a .xlsx file into a pandas dataframe
        xls_file = pd.ExcelFile(url)
        df = xls_file.parse(worksheet, converters={'start': str, 'end': str, 'trend_i': str})
        self.df = df

        # parse settings file (in .ini file)
        parser = ConfigParser()
        parser.read(settingf)
        self.settingf = settingf
        self.settings = parser

    def fetch_tradelist(self):
        '''
        This function will produce a TradeList object
        using self.url

        Returns
        -------
        TradeList
        '''

        trade_list = []
        for index, row in self.df.iterrows():
            print("Processing trade with id: {0}".format(row['id']))
            pair = row['id'].split(" ")[0]
            t = Trade(
                start=row['start'],
                entry=row['entry'],
                SL=row['SL'],
                TP=row['TP'],
                SR=row['SR'],
                type=row['type'],
                timeframe=row['timeframe'],
                strat=row['strat'],
                id=row['id'],
                pair=pair,
                settingf=self.settingf)
            trade_list.append(t)

        tl = TradeList(settingf=self.settingf,
                       tlist=trade_list)
        return tl

    def write_tradelist(self, trade_list):
        '''
        Write the TradeList to the Excel spreadsheet
        pointed by the TradeJournal

        Parameters
        ----------
        tradelist : TradeList, Required

        Returns
        -------
        Nothing
        '''

        assert self.settings.has_option('trade_journal', 'worksheet_name'), \
            "'worksheet_name' needs to be defined"

        # get colnames to print in output worksheet from settings
        assert self.settings.has_option('trade_journal', 'colnames'), "'colnames' needs to be defined"
        colnames = self.settings.get('trade_journal', 'colnames').split(",")

        data = []
        for t in trade_list.tlist:
            row = []
            for a in colnames:
                value = None
                try:
                    value = getattr(t, a)
                    if isinstance(value, PivotList):
                        dt_l = value.print_pivots_dates()
                        value = [d.strftime('%d/%m/%Y:%H:%M') for d in dt_l]
                except:
                    warnings.warn("Error getting value for attribute: {0}".format(a))
                    value = "n.a."
                row.append(value)
            data.append(row)
        df = pd.DataFrame(data, columns=colnames)

        book = load_workbook(self.url)
        writer = pd.ExcelWriter(self.url, engine='openpyxl')
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        df.to_excel(writer, self.settings.get('trade_journal', 'worksheet_name'))
        writer.save()


