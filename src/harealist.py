import pdb

from configparser import ConfigParser

class HAreaList(object):
    '''
    Class that represents a list of HArea objects

    Class variables
    ---------------
    halist : list, Required
            List of HArea objects
    settingf : str, Optional
               Path to *.ini file with settings
    settings : ConfigParser object generated using 'settingf'
    '''

    def __init__(self, halist, settingf=None, settings=None):
        self.settingf = settingf
        self.halist = halist

        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

    def onArea(self, candle):
        '''
        Function that will check which (if any) of the HArea objects
        in this HAreaList will overlap with 'candle'.

        See comments in code to understand what is considered
        an overlap

        Parameters
        ----------
        candle: BidAskCandle object

        Returns
        -------
        An HArea object overlapping with 'candle'.
        None if there are no HArea objects overlapping
        '''
        if not hasattr(candle, 'colour'):
            candle.set_candle_features()

        onArea_hr = None
        for harea in self.halist:
            highAttr = "high{0}".format(self.settings.get('general', 'bit'))
            lowAttr = "low{0}".format(self.settings.get('general', 'bit'))
            if harea.price <= getattr(candle, highAttr) and harea.price >= getattr(candle, lowAttr):
                    onArea_hr = harea

        return onArea_hr

    def print(self):
        '''
        Function to print out basic information on each of the
        HArea objects in the HAreaList

        Returns
        -------
        Nothing
        '''
        print("#pair timeframe upper-price-lower no_pivots tot_score")
        for harea in self.halist:
            print("{0} {1} {2}-{3}-{4} {5} {5}".format(harea.instrument,
                                                       harea.granularity,
                                                       harea.upper,
                                                       harea.price,
                                                       harea.lower,
                                                       harea.no_pivots,
                                                       harea.tot_score))


    def __repr__(self):
        return "HAreaList"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str
print("this is master")