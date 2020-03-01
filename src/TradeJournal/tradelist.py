from configparser import ConfigParser


class TradeList(object):
    '''
    Class that represents a list of Trade objects

    Class variables
    ---------------
    tlist : list, Required
            List of Trade objects
    '''

    def __init__(self, tlist, settingf):
        self.settingf = settingf
        self.tlist = tlist
        # parse settings file (in .ini file)
        parser = ConfigParser()
        parser.read(settingf)
        self.settings = parser

    def analyze(self):
        '''
        Analyze each of the Trade objects in TradeList depending
        on value of settings.get('trade_journal', 'strats')
        :return:
        '''