import pandas as pd
import numpy as np
import logging
import math
import re
from trading_journal.trade import Trade
from openpyxl import load_workbook, Workbook
from config import CONFIG

# create logger
tj_logger = logging.getLogger(__name__)
tj_logger.setLevel(logging.INFO)

class TradeJournal(object):
    '''
    Constructor

    Class variables
    ---------------
    url: path to the .xlsx file with the trade journal
    worksheet: str, Required
               Name of the worksheet that will be used to create the object.
               i.e. trading_journal
    '''

    def __init__(self, url, worksheet):
        self.url = url
        self.worksheet = worksheet

        #read-in the 'trading_journal' worksheet from a .xlsx file into a pandas dataframe
        try:
            xls_file = pd.ExcelFile(url)
            df = xls_file.parse(worksheet, converters={'start': str, 'end': str, 'trend_i': str})
            if df.empty is True:
                raise Exception("No trades fetched for url:{0} and worksheet:{1}".format(self.url, self.worksheet))
            # replace n.a. string by NaN
            df = df.replace('n.a.', np.NaN)
            # remove trailing whitespaces from col names
            df.columns = df.columns.str.rstrip()
            self.df = df
        except FileNotFoundError:
            wb = Workbook()
            wb.create_sheet(worksheet)
            wb.save(str(self.url))

    def fetch_trades(self, init_period=False):
        '''
        Function to fetch a list of Trade objects

        Parameter
        ---------
        init_period : bool
                      If true, then the CandleList
                      used for the 'period' class attribute
                      will be initialized. Default: False

        Return
        ------
        list with trades
        '''
        trade_list = []
        args = {}
        for index, row in self.df.iterrows():
            pair = re.split(r'\.| ', row['id'])[0]
            args = {'pair': pair}
            for c in row.keys():
                args[c] = row[c]
            if init_period is True:
                t = Trade(**args, init=True)
            else:
                t = Trade(**args)
            trade_list.append(t)

        return trade_list

    def win_rate(self, strats):
        '''
        Calculate win rate and pips balance
        for this TradeJournal. If outcome attrb is not
        defined then it will invoke the run_trade method
        on each particular trade

        Parameters
        ----------
        strats : str
                 Comma-separated list of strategies to analyse: i.e. counter,counter_b1

        Returns
        -------
        int : number of successes
        int : number of failures
        pips : pips balance in this TradeList
        '''

        strat_l = strats.split(",")
        number_s = number_f = tot_pips = 0
        for index, row in self.df.iterrows():
            pair = row['id'].split(" ")[0]
            args = {'pair': pair}
            for c in row.keys():
                args[c] = row[c]
            t = Trade(**args)
            if t.strat not in strat_l:
                continue
            if not hasattr(t, 'outcome') or math.isnan(t.outcome):
                t.run_trade(expires=1)
            if t.outcome == 'success':
                number_s += 1
            elif t.outcome == 'failure':
                number_f += 1
            tot_pips += t.pips
        tot_pips = round(tot_pips, 2)
        tot_trades = number_s+number_f
        perc_wins = round(number_s*100/tot_trades, 2)
        perc_losses = round(number_f*100/tot_trades, 2)
        print("Tot number of trades: {0}\n-------------".format(tot_trades))
        print("Win trades: {0}; Loss trades: {1}".format(number_s, number_f))
        print("% win trades: {0}; % loss trades: {1}".format(perc_wins, perc_losses))
        print("Pips balance: {0}".format(tot_pips))

        return number_s, number_f, tot_pips

    def write_tradelist(self, trade_list, sheet_name):
        '''
        Write the TradeList to the Excel spreadsheet
        pointed by the trade_journal

        Parameters
        ----------
        trade_list : List of Trade objects, Required
        sheet_name : worksheet name

        Returns
        -------
        Nothing
        '''
        colnames = CONFIG.get("trade_journal", "colnames").split(",")

        data = []
        for t in trade_list:
            row = []
            for key in colnames:
                # some keys are not defined for some of the Trade
                # objects
                if key in t.__dict__:
                    row.append(t.__dict__[key])
                else:
                    row.append("n.a.")
            data.append(row)

        df = pd.DataFrame(data, columns=colnames)

        book = load_workbook(self.url)
        writer = pd.ExcelWriter(self.url, engine='openpyxl')
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        tj_logger.info("Creating new worksheet with trades with name: {0}".
                       format(sheet_name))
        df.to_excel(writer, sheet_name)
        writer.save()
