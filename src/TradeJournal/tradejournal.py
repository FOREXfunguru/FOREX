import pandas as pd
import pdb
import re
import math
import warnings
from TradeJournal.trade import Trade
from openpyxl import load_workbook
from Pattern.counter import Counter
from Pattern.counter_dbtp import CounterDbTp

class TradeJournal(object):
    '''
    Constructor

    Class variables
    ---------------
    
    url: path to the .xlsx file with the trade journal
    worksheet: str, Required
               Name of the worksheet that will be used to create the object. i.e. trading_journal
    '''

    def __init__(self, url, worksheet):
        self.url=url
        self.worksheet=worksheet
        #read-in the 'trading_journal' worksheet from a .xlsx file into a pandas dataframe
        xls_file = pd.ExcelFile(url)
        df = xls_file.parse(worksheet,converters={'start': str, 'end': str, 'trend_i': str})
        self.df=df

    def print_winrate(self,strat=None):
        '''
        Function to print the win rate proportion and also the profit in pips

        Parameters
        ----------
        strat : String, Optional
                If defined, then select all trades of a certain type.
                Possible values are: 'counter_doubletop'
        '''

        DF=None
        if strat is not None:
            DF=self.df[self.df['strat'] == strat]
        else:
            DF=self.df

        print("Number of records: {0}".format(DF.shape[0]))

        for index, row in DF.iterrows():
            # get pair from id
            pair = row['id'].split(' ')[0]

            attrbs = row.to_dict()
            t = Trade(pair=pair, **attrbs)
            outcome_seen=True

            if not hasattr(t, 'outcome'):
                outcome_seen=False
            else:
                x = float(t.outcome)
                if math.isnan(x):
                    outcome_seen = False

            if not hasattr(t, 'TP'):
                assert hasattr(t, 'RR'), "Neither the RR not the TP is defined. Please provide RR"
                diff = (t.entry - t.SL) * t.RR
                t.TP = round(t.entry + diff, 4)

            if outcome_seen is False:
                t.run_trade()
                DF.loc[index, 'outcome'] = t.outcome
                DF.loc[index, 'pips'] = t.pips
                DF.loc[index, 'TP'] = t.TP

        pdb.set_trace()
        print("Proportion of outcome:\n{0}".format(DF.loc[:,'outcome'].value_counts()))
        print("Sum of pips:\n{0}".format(DF['pips'].sum()))


    def fetch_trades(self,run=False, strat=None):
        '''
        This function will fetch the trades that are in this TradingJournal and will create an independent
        Trade object for each record

        Parameters
        ----------
        run : bool, Optional
              Execute trade. Default=False
        strat : String, Optional
                If defined, then select all trades of a certain type.
                Possible values are: 'counter_doubletop'

        Returns
        ------
        list
             List with Trade objects
        '''

        trade_list=[]
        for index,row in self.df.iterrows():
            print("Processing trade with id: {0}".format(row['id']))
            if strat is not None:
                if strat!=row['strat']:
                    continue
            #get pair from id
            pair=row['id'].split(' ')[0]

            attrbs={}
            for items in row.iteritems():
                attrbs[items[0]]=items[1]

            # behave depending on identified pattern
            c=None
            if strat=="counter":
                c=Counter(pair=pair,**attrbs)
                c.init_feats()
            elif strat=="counter_doubletop":
                c=CounterDbTp(pair=pair, **attrbs)
                c.init_feats()
                c.init_trend_feats()

            p = re.compile('clist_')
            attrbs1={}

            for attr, value in c.__dict__.items():
                if p.match(attr):continue
                if type(value) is list:
                    if attr == 'rsibounces_lengths':
                        attrbs1[attr] = value
                    else:
                        attrbs1[attr]=len(value)
                else:
                    attrbs1[attr] = value

            t=Trade(strat=row['strat'],**attrbs1)

            if run is True:
                t.run_trade()
            trade_list.append(t)

        return trade_list

    def write_trades(self, trade_list, colnames):
        '''
        Write the trade_list to the Excel spreadsheet
        pointed by the TradeJournal

        Parameters
        ----------
        trade_list : list, Required
                     List with Trade objects
        colnames : list, Required
                    Column names that will control the order
                    of the columns

        Returns
        -------
        Nothing
        '''

        p = re.compile('bounce_')
        data=[]
        for t in trade_list:
            row=[]
            for a in colnames:
                value=None
                try:
                    value=getattr(t, a)
                    if p.match(a):
                        value=value[0]
                except:
                    warnings.warn("Error getting value for attribute: {0}".format(a))
                    value="n.a."
                row.append(value)
            data.append(row)
        df = pd.DataFrame(data, columns=colnames)

        book = load_workbook(self.url)
        writer = pd.ExcelWriter(self.url, engine='openpyxl')
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        df.to_excel(writer, 'calculated_trades')
        writer.save()

    def add_trend_momentum(self):
        '''
        This function will add a new worksheet named 'trend_momentum' to the .xlsx file
        For this, the function will perform some queries to the Oanda's REST API and will
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
