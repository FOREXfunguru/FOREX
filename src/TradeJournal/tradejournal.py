import pandas as pd
import pdb
import re
import math
import warnings
from TradeJournal.trade import Trade
from TradeJournal.tradelist import TradeList
from openpyxl import load_workbook
from configparser import ConfigParser

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

    def print_winrate(self, worksheet_name=None):
        '''
        Function to print the win rate proportion and also the profit in pips

        Parameters
        ----------
        worksheet_name : String, Optional
                         Name given to output worksheet

        Returns
        -------
        Proportion of outcome
        Total sum of pips
        Number of observations and a .xlsx with a worksheet with output
        '''

        # get strats to analyse from settings
        assert self.settings.has_option('trade_journal', 'strats'), "'strats' needs to be defined"
        strats = self.settings.get('trade_journal', 'strats').split(",")

        print("Number of records: {0}".format(self.df.shape[0]))
        trades_seen = False
        for index, row in self.df.iterrows():
            if row['strat'] not in strats:
                continue
            else:
                trades_seen = True

            # get pair from id
            pair = row['id'].split(' ')[0]
            attrbs = row.to_dict()

            t = Trade(pair=pair, **attrbs)
            outcome_seen = True

            if not hasattr(t, 'outcome'):
                outcome_seen = False
            else:
                x = float(t.outcome)
                if math.isnan(x):
                    outcome_seen = False

            if not hasattr(t, 'TP') or math.isnan(t.TP) is True:
                assert hasattr(t, 'RR'), "Neither the RR not" \
                                         " the TP is defined. Please provide RR"
                diff = (t.entry - t.SL) * t.RR
                t.TP = round(t.entry + diff, 4)

            if outcome_seen is False:
                t.run_trade()
                self.df.loc[index, 'outcome'] = t.outcome
                self.df.loc[index, 'pips'] = t.pips
                self.df.loc[index, 'TP'] = t.TP

        outcome_prop = self.df.loc[:, 'outcome'].value_counts()
        sum_pips = self.df['pips'].sum()

        if self.settings('trading_journal', 'write_xlsx') is True:
            sheet_name = None
            if worksheet_name is not None:
                sheet_name = "outcome_{0}".format(worksheet_name)
            else:
                sheet_name = "outcome_{0}".format(strat)

            book = load_workbook(self.url)
            writer = pd.ExcelWriter(self.url, engine='openpyxl')
            writer.book = book
            writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
            DF.to_excel(writer, sheet_name)
            writer.save()

        return (outcome_prop, sum_pips, DF.shape[0])

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

        pt = re.compile('bounces')
        data = []
        for t in trade_list:
            row = []
            for a in colnames:
                value = None
                try:
                    value = getattr(t, a)
                    if pt.match(a):
                        # iterate over PivotList
                        date_str = ""
                        for p in value.plist:
                            date_str += p.candle.time.strftime('%d/%m/%Y:%H:%M')+","
                        value = date_str
                except:
                    warnings.warn("Error getting value for attribute: {0}".format(a))
                    value = "n.a."
                row.append(value)
            data.append(row)
        df = pd.DataFrame(data, columns=self.settings.get('trade_journal', 'colnames'))

        book = load_workbook(self.url)
        writer = pd.ExcelWriter(self.url, engine='openpyxl')
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        df.to_excel(writer, )
        writer.save()

    def add_trend_momentum(self):
        '''
        This function will add a new worksheet named 'trend_momentum' to the .xlsx file
        For this, the function will pers
        form some queries to the Oanda's REST API and will
        parse the results
        '''

        trade_list=self.fetch_trades()
        data=[]
        for trade in trade_list:
            print("Processing: {0}".format(trade.start.strftime("%d-%m-%y")))
            if trade.timeframe=="H10":
                warnings.warn("Timeframe format: {0} is not valid. Skipping".format(trade.timeframe))
                continue
            if trade.timeframe=="na":
                warnings.warn("Timeframe is not defined. Skipping")
                continue
            row=[]
            row.extend((trade.start, trade.end, trade.pair, trade.type, trade.timeframe, trade.outcome))
            cl=trade.fetch_candlelist()
            if cl.len==1:
                warnings.warn("CandleList has only one candle. Skipping")
                continue
            cl.calc_binary_seq(merge=True)
            cl.calc_number_of_0s(norm=True)
            cl.calc_number_of_doubles0s(norm=True)
            cl.calc_longest_stretch()
            cl.get_entropy(norm=True)

            for i in ['high','low','open','close','colour','merge']:
                row.append("'{0}'".format(cl.seq[i]))
            for i in ['high','low','open','close','colour','merge']:
                row.append(cl.number_of_0s[i])
            for i in ['high','low','open','close','colour']:
                row.append(cl.longest_stretch[i])
            for i in ['high','low','open','close','colour']:
                row.append(cl.entropy[i])
            row.extend((cl.highlow_double0s,cl.openclose_double0s))
            data.append(row)

        columns=['start','end','pair','type','timeframe','outcome','high','low','open','close','colour','merge',
                 'No_of_0s_high','No_of_0s_low','No_of_0s_open','No_of_0s_close','No_of_0s_colour','No_of_0s_merge',
                 'stretch_high','stretch_low','stretch_open','stretch_close','stretch_colour',
                 'ent_high','ent_low','ent_open','ent_close','ent_colour',
                 'No_of_double0_higlow','No_of_double0_openclose']
        df=pd.DataFrame(data,columns=columns)
        book = load_workbook(self.url)
        writer = pd.ExcelWriter(self.url, engine='openpyxl') 
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        df.to_excel(writer,'trend_momentum')
        writer.save()
