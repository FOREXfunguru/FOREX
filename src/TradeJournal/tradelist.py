from configparser import ConfigParser
import pdb
from Pattern.counter import Counter

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
        on value of settings.get('counter', 'strats') and add the
        calculated attributes to Trade

        :returns
        TradeList
        '''

        #these are the strategies that will be analysed using the Counter pattern
        strats = self.settings.get('counter', 'strats').split(",")

        trade_list=[]
        for t in self.tlist:
            if t.strat in strats:
                t.run_trade()
                c = Counter(trade=t,
                            settingf=self.settingf,
                            init_feats=True)
                pdb.set_trace()
                attrb_ls = self.settings.get('counter', 'attrbs').split(",")
                for a in attrb_ls:
                    # add 'a' attribute to Trade object
                    setattr(t, a, getattr(c, a))
            trade_list.append(t)
        tl = TradeList(settingf=self.settingf,
                       tlist=trade_list)

        return tl