from scipy import stats
import pandas as pd
import pdb
import re


class CandleList(object):
    '''
    Constructor

    Class variables
    ---------------
    clist : list, Required
            List of Candle objects
    type : str, Optional
           Type of this CandleList. Possible values are 'long'/'short'
    seq : dict, Optional
          Dictionary containing the binary seq for the different candle portions
    number_of_0s : dict, Optional
          Dictionary containing the number of 0s (possibly normalized) in the different
          binary seqs in self.seq
    longest_stretch : dict, Optional
           Dictionary containing the longest stretch of 0s in the different binary seqs
           in self.seq
    highlow_double0s : number, Optional
          Number of double 0s in the high/low of the candles in CandleList
    openclose_double0s : number, Optional
          Number of double 0s in the open/close of the candles in CandleList
    entropy : Dict of Floats, Optional
          Entropy for each of the sequences in self.seq 
    '''

    def __init__(self, clist,type=None,seq=None, number_of_0s=None,
                 longest_stretch=None, highlow_double0s=None, 
                 openclose_double0s=None, entropy=None):
        self.clist=clist
        self.type=type
        self.len=len(clist)
        self.seq=seq
        self.number_of_0s=number_of_0s
        self.longest_stretch=longest_stretch
        self.highlow_double0s=highlow_double0s
        self.openclose_double0s=openclose_double0s
        self.entropy=entropy
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

    def calc_binary_seq(self, merge=True):
        '''
        Calculate the sequence of 1s and 0s corresponding to the progression of the candles in
        the trend. For example, if the CandleList is  is of type='short',then 
        '111' means that there are 3 candles for which each of the candle highs mark lower
        highs

        Parameters
        ----------
        merge : bool, Optional
                If true, then the function will calculate a merged binary sequence produced after concatenating the seqs
                for the different portions of the candle (i.e. 'high','low','open','close','colour')
        
        Returns
        ------
        Nothing
        '''

        adict={}
        for p in ['high','low','open','close','colour']:
            portion="{0}Bid".format(p)

            if p is "colour":
                bin_string=""
                for c in self.clist:
                    c.set_candle_features()
                    if self.type=='long' and c.colour== "green":
                        bin_string+="1"
                    elif self.type=='long' and c.colour=="red":
                        bin_string+="0"
                
                    if self.type=='short' and c.colour=="green":
                        bin_string+="0"
                    elif self.type=='short' and c.colour=="red":
                        bin_string+="1"
                adict['colour']=bin_string
                if merge is True:
                    if 'merge' in adict:
                        adict['merge']=adict['merge']+bin_string
                    else:
                        adict['merge']=bin_string
            else:
                bin_string=""
                p_candle=None
                for c in self.clist:
                    if p_candle is None:
                        p_candle = getattr(c, portion)
                    else:
                        res=getattr(c, portion)-p_candle
                        res= float('%.7f' % res)
                        if self.type=='long' and res>0:
                            bin_string+="1"
                        elif self.type=='long' and res<0:
                            bin_string+="0"
                        elif self.type=='long' and res==0:
                            bin_string+="N"
                        
                        if self.type=='short' and res>0:
                            bin_string+="0"
                        elif self.type=='short' and res<0:
                            bin_string+="1"
                        elif self.type=='short' and res==0:
                            bin_string+="N"

                        p_candle = getattr(c, portion)
                adict[p]=bin_string
                if merge is True:
                    if 'merge' in adict:
                        adict['merge']=adict['merge']+bin_string
                    else:
                        adict['merge']=bin_string
        self.seq=adict

    def calc_number_of_0s(self, norm=True):
        '''
        This function will calculate the number of 0s
        in self.seq (i.e. 00100=4)

        Parameters
        ----------
        norm: bool, Optional
              If True then the calculated value will
              be normalized by length. Default: True

        Returns
        -------
        Nothing
        '''

        a_dict={}
        for key in self.seq:
            sequence=self.seq[key]
            a_list=list(sequence)
            new_list=[a_number for a_number in a_list if a_number=='0']
            number_of_0s=0
            if norm is True:
                number_of_0s=len(new_list)/len(a_list)
            else:
                number_of_0s=len(new_list)
            a_dict[key]=number_of_0s
     
        self.number_of_0s=a_dict

    def get_entropy(self, norm=True):
        '''
        Calculates the entropy for each of the sequences in self.seq

        Parameters
        ----------
        norm: bool, Optional
              If True then the calculated value will
              be normalized by length. Default: True

        Returns
        -------
        Nothing
        '''

        a_dict={}
        for key in ['high','low','open','close','colour']:
            s_list=list(self.seq[key])
            data = pd.Series(s_list)
            p_data= data.value_counts()/len(data) # calculates the probabilities
            entropy=stats.entropy(p_data)  # input probabilities to get the entropy
            f_entropy=None
            if norm is True:
                f_entropy=entropy/len(s_list)
            else:
                f_entropy
            a_dict[key]=f_entropy
        
        self.entropy=a_dict

    def __get_number_of_double0s(self,seq1,seq2,norm=True):
        '''
        This function will detect the columns having 2 0s in an alignment.
        For example:
        10100111
        11001000
        Will have 1 double 0

        Parameters
        ----------
        seq1: str, Required
        seq2: str, Required
        norm: bool, Optional
              If True then the returned value will
              be normalized by length. Default: True

        Returns
        -------
        A float
        '''
        list1=list(seq1)
        list2=list(seq2)

        if len(list1) != len(list2):
            raise Exception("Lengths of seq1 and seq2 are not equal")

        number_of_double0s=0
        for i, j in zip(list1, list2):
            if i is "N" or j is "N":
                print("Skipping this column as there is a N in the binary seq")
                continue
            if int(i)==0 and int(j)==0:
                number_of_double0s=number_of_double0s+1

        if norm is True:
            return number_of_double0s/len(list1)
        else:
            return number_of_double0s

    def calc_number_of_doubles0s(self,norm=True):
        '''
        This function will set the 'highlow_double0s' and 'openclose_double0s'
        class members
        '''

        high_low=self.__get_number_of_double0s(self.seq['high'], self.seq['low'], norm=norm)
        open_close=self.__get_number_of_double0s(self.seq['open'], self.seq['close'], norm=norm)
        
        self.highlow_double0s=high_low
        self.openclose_double0s=open_close
        
    def calc_longest_stretch(self):
        '''
        This function will calculate the longest stretch of contiguous 0s.

        For example:
        1010000111

        Will return 4

        Returns
        -------
        Nothing
        '''
        a_dict={}
        for key in ['high','low','open','close','colour']:
            sequence=self.seq[key]
            length=len(max(re.compile("(0+0)*").findall(sequence)))
            a_dict[key]=length

        self.longest_stretch=a_dict

    def calc_rsi(self):
        '''
        Calculate the RSI for a certain candle list

        Returns
        -------
        Nothing
        '''

        series=[]
        for c in self.clist:
            series.append(c.closeAsk)

        df = pd.DataFrame({'close': series})
        chg = df['close'].diff(1)

        gain = chg.mask(chg < 0, 0)
        loss = chg.mask(chg > 0, 0)

        rsi_period = 14
        avg_gain = gain.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
        avg_loss = loss.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()

        rs = abs(avg_gain / avg_loss)

        rsi = 100 - (100 / (1 + rs))

        ix=0
        for c,v in zip(self.clist,rsi):
            self.clist[ix].rsi=v
            ix+=1

    def calc_rsi_bounces(self):
        '''
        Calculate the number of times that the
        price has been in overbought (>70) or
        oversold(<30) regions

        Returns
        -------
        dict
             {number: 3
             lengths: [4,5,6]}
        Where number is the number of times price
        has been in overbought/oversold and lengths list
        is formed by the number of candles that the price
        has been in overbought/oversold each of the times

        '''

        adj=False
        init=False
        num_times=0
        length=0
        lengths=[]

        for c in self.clist:
            if c.rsi is None: raise Exception("RSI values are not defined for this Candlelist, "
                                              "run calc_rsi first")
            print(c.rsi)
            if (c.rsi==41.29603413309367):
                print(pdb.set_trace())

            if (c.rsi>70 or c.rsi<30) and adj is False:
                num_times+=1
                length+=1
                adj=True
            elif (c.rsi>70 or c.rsi<30) and adj is True:
                length+=1
            elif (c.rsi<70 and c.rsi>30):
                if adj is True: lengths.append(length)
                length=0
                adj=False
