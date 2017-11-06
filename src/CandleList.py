from OandaAPI import Candle
import pdb
import re


class CandleList(object):
    '''
    Constructor

    Class variables
    ---------------
    clist : list, Required
            List of Candle objects
    '''

    def __init__(self, clist):
        self.clist=clist
        self.len=len(clist)
        self.ix=0

    def __iter__(self):
        return self

    def __next__(self):
        if self.ix < self.len:
            candle=self.clist[self.ix]
            self.ix += 1
            return candle
        else:
            raise StopIteration()
    next = __next__  # python2.x compatibility.

    def get_binary_seq(self,type,p):
        '''
        Get a sequence of 1s and 0s corresponding to the progression of the candles in
        the trend. For example, if the funtion is run with type='short',p='high' then 
        '111' means that there are 3 candles for which each of the candle highs mark lower
        highs

        Parameters
        ----------
        type : string, Required
               Type of the trade corresponding to this clist. Possible values are:
               long/short
        p : string, Required
            Use candle highs/lows or open/close or colour for calculating the sequence.
            Possible values are: 'high','low','open','close','colour'
        
        Returns
        ------
        A str composed of 1s and 0s
        '''

        portion="{0}Bid".format(p)
        portion= re.sub('colourBid','colour',portion)

        bin_string=""

        if portion is "colour":
            for c in self.clist:
                c.set_candle_features()
                if type is 'long' and c.colour is "green":
                    bin_string+="1"
                elif type is 'long' and c.colour is "red":
                    bin_string+="0"
                
                if type is 'short' and c.colour is "green":
                    bin_string+="0"
                elif type is 'short' and c.colour is "red":
                    bin_string+="1"
                
        else:
            p_candle=None
            for c in self.clist:
                if p_candle is None:
                    p_candle = getattr(c, portion)
                else:
                    res=getattr(c, portion)-p_candle
                    res= float('%.4f' % res)
                    if type is 'long' and res>0:
                        bin_string+="1"
                    elif type is 'long' and res<0:
                        bin_string+="0"
                        
                    if type is 'short' and res>0:
                        bin_string+="0"
                    elif type is 'short' and res<0:
                        bin_string+="1"

                    p_candle = getattr(c, portion)

        return bin_string
