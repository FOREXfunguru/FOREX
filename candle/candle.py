'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''

from oanda.connect import Connect
from config import CONFIG

class Candle(object):
    """
    Constructor

    Class variables
    ---------------
    dict_data : dict
                Dictionary with data as genererated by
                the Oanda REST API
    """
    def __init__(self, dict_data):
        for key in dict_data:
            setattr(self, key, dict_data[key])

    def set_candle_features(self):
        '''
        Set basic candle features based on price
        i.e. self.colour, upper_wick, midAsk or midBid, etc...
        '''
        if not self.openBid or not self.closeBid:
            raise Exception("Either self.openBid or self.closeBid need to be set to invoke set_candle_pattern")

        if not self.highBid or not self.lowBid:
            raise Exception("Either self.highBid or self.lowBid need to be set to invoke set_candle_pattern")

        upper = lower = 0.0
        if self.openBid < self.closeBid:
            self.colour = "green"
            upper = self.closeBid
            lower = self.openBid
        elif self.openBid > self.closeBid:
            self.colour = "red"
            upper = self.openBid
            lower = self.closeBid
        else:
            self.colour = "undefined"
            upper = self.openBid
            lower = self.closeBid

        #calculating mid*
        self.midAsk = round(abs(self.highAsk + self.lowAsk)/2, 4)
        self.midBid = round(abs(self.highBid + self.lowBid)/2, 4)

        self.upper_wick = round(self.highBid - upper, 4)
        self.lower_wick = round(lower - self.lowBid, 4)

        height = self.highBid - self.lowBid
        body = abs(self.openBid - self.closeBid)

        # perc of total height that body will represent
        if height == 0 or body == 0:
            perc_body = 0
            perc_uwick = 0
            perc_lwick = 0
        else:
            perc_body = round((body * 100) / height, 2)
            # perc of total height that 'upper_wick' will represent
            perc_uwick = round((self.upper_wick * 100) / height, 2)
            # perc of total height that 'lower_wick' will represent
            perc_lwick = round((self.lower_wick * 100) / height, 2)

        self.perc_body = perc_body
        self.perc_uwick = perc_uwick
        self.perc_lwick = perc_lwick

    def indecision_c(self, ic_perc=10):
        '''
        Function to check if 'self'
        is an indecision candle

        Parameters
        ----------
        ic_perc : int
                  Candle's body percentage below which the candle will be considered
                  indecision candle
                  Default : 10
        Returns
        -------
        boolean: True if it is an indecision candle. False otherwise
        '''

        if self.perc_body <= ic_perc:
            return True
        else:
            return False

    def set_formation(self):
        '''
        Set candle formation

        Note: These are the conventions I will follow:

        DOJI: Body is <=10% of the total candle height
        '''

        if self.openBid is None or self.closeBid is None:
            raise Exception("Either self.openBid or self.closeBid need to be set to invoke set_candle_pattern")

        if self.highBid is None or self.lowBid is None:
            raise Exception("Either self.highBid or self.lowBid need to be set to invoke set_candle_pattern")

        if self.upper_wick is None or self.lower_wick is None:
            raise Exception("Either self.upper_wick or self.lower_wick need to be set to invoke set_candle_formation")

        if self.perc_body < 35 and self.perc_lwick > 60 and self.colour == "green":
            self.representation = "hammer"
        elif self.perc_body < 35 and self.perc_lwick > 60 and self.colour == "red":
            self.representation = "hanging_man"
        elif self.perc_body < 40 and self.perc_uwick > 55 and self.colour == "green":
            self.representation = "inverted_hammer"
        elif self.perc_body < 40 and self.perc_uwick > 55 and self.colour == "red":
            self.representation = "shooting_star"
        elif self.perc_body < 4 and self.perc_uwick > 40 and self.perc_lwick > 40:
            self.representation = "doji"
        elif self.perc_body < 4 and self.perc_uwick < 2 and self.perc_lwick > 94:
            self.representation = "dragonfly_doji"
        elif self.perc_body < 4 and self.perc_uwick > 94 and self.perc_lwick < 2:
            self.representation = "gravestone_doji"
        elif self.perc_body > 90 and self.colour == "green":
            self.representation = "green_marubozu"
        elif self.perc_body > 90 and self.colour == "red":
            self.representation = "red_marubozu"
        else:
            self.representation = "undefined"

    def __repr__(self):
        return "Candle"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str