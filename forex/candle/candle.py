'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''

from api.oanda.connect import Connect
from utils import *

class Candle(object):
    """Class representing a particular Candle"""
    def __init__(self, **kwargs)->None:
        allowed_keys = ['complete', 'volume', 'time', 'mid' ] # allowed arbitrary argsa
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        self.__dict__.update((k, float(v)) for k, v in self.mid.items())
        self._colour = self._set_colour()
        self._upper_wick = 0.0
        self._lower_wick = 0.0
        self._perc_body = 0.0
        self._perc_uwick = 0.0
        self._perc_lwick = 0.0
        self.set_candle_features()

    @property
    def colour(self)->str:
        """Candle's body colour"""
        return self._colour

    @property
    def upper_wick(self)->float:
        """Candle's upper wick"""
        return self._upper_wick

    @property
    def lower_wick(self)->float:
        """Candle's lower wick"""
        return self._lower_wick
    
    @property
    def perc_body(self)->float:
        """Candle's perc_body"""
        return self._perc_body
    
    @property
    def perc_uwick(self)->float:
        """Candle's perc_uwick"""
        return self._perc_uwick
    
    @property
    def perc_lwick(self)->float:
        """Candle's perc_lwick"""
        return self._perc_lwick

    def _set_colour(self)->str:
        if self.o < self.c:
            return "green"
        elif self.o > self.c:
            return "red"
        else:
            return "undefined"

    def set_candle_features(self):
        """Set basic candle features based on price
        i.e. upper_wick, midAsk or midBid, etc..."""
        upper = lower = 0.0
        if self.o < self.c:
            upper = self.c
            lower = self.o
        elif self.o > self.c:
            upper = self.o
            lower = self.c

        self._upper_wick = round(self.h - upper, 4)
        self._lower_wick = round(lower - self.l, 4)

        height = self.h - self.l
        body = abs(self.o- self.c)

        # perc of total height that body will represent
        if height == 0 or body == 0:
            perc_body = perc_uwick = perc_lwick = 0
        else:
            perc_body = round((body * 100) / height, 2)
            # perc of total height that 'upper_wick' will represent
            perc_uwick = round((self.upper_wick * 100) / height, 2)
            # perc of total height that 'lower_wick' will represent
            perc_lwick = round((self.lower_wick * 100) / height, 2)

        self._perc_body = perc_body
        self._perc_uwick = perc_uwick
        self._perc_lwick = perc_lwick

    def indecision_c(self, ic_perc: int=10)->bool:
        """Function to check if 'self' is an indecision candle.

        Args:
            ic_perc : Candle's body percentage below which the candle will be considered 
                      indecision candle.
        """
        if self.perc_body <= ic_perc:
            return True
        else:
            return False

    def volatile_c(self, diff_cutoff: int, bit: str, pair: str )->bool:
        """Function to check if the candle is volatile. This means
        that the difference between Candle's high and low is greater than
        'diff'.

        Args:
            diff_cutoff : Number of pips used as the cutt-off above which
                          the candle is considered volatile. It is basically
                          the diff in pips between high and Low of the candle.
            bit : Candle bit used. i.e. Ask or Bid
            pair : Instrument
        """
        u_attr = "high{0}".format(bit)
        l_attr = "low{0}".format(bit)
        diff_in_price = self.h-self.l
        diff_in_pips = float(calculate_pips(pair, diff_in_price))

        if diff_in_pips > diff_cutoff:
            return True
        else :
            return False

    def __repr__(self):
        return "Candle"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str