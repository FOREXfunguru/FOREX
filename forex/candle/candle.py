'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
from utils import *

class Candle(object):
    """Class representing a particular Candle"""
    def __init__(self, **kwargs)->None:
        allowed_keys = ['complete', 'volume', 'time', 'o','h','c','l'] # allowed arbitrary argsa
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        numeric = ['o', 'h', 'c', 'l']
        self.__dict__.update((k, float(v)) for k,v in self.__dict__.items() if k in numeric)
        self._colour = self._set_colour()
        self._perc_body = self._calc_perc_body()

    @property
    def colour(self)->str:
        """Candle's body colour"""
        return self._colour
    
    @property
    def perc_body(self)->float:
        """Candle's body percentage"""
        return self._perc_body

    def _set_colour(self)->str:
        if self.o < self.c:
            return "green"
        elif self.o > self.c:
            return "red"
        else:
            return "undefined"
    
    def _calc_perc_body(self)->float:
        height = self.h - self.l
        body = abs(self.o- self.c)
        return round((body * 100) / height, 2)

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

    def __repr__(self):
        return "Candle"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str