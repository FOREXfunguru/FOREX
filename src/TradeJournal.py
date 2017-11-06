import pandas as pd

class TradeJournal(object):
    '''
    Constructor

    Class variables
    ---------------
    
    url: path to the .xlsx file with the trade journal
    '''

    def __init__(self, url):
        self.url=url
        #read-in the 'trading_journal' worksheet from a .xlsx file into a pandas dataframe
        xls_file = pd.ExcelFile(url)
        df = xls_file.parse('trading_journal')
        self.df=df

