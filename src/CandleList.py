from scipy import stats
from OandaAPI import OandaAPI
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import pandas as pd
import pdb
from datetime import timedelta,datetime,time
import re
import peakutils
import numpy as np
import matplotlib

matplotlib.use('PS')
import matplotlib.pyplot as plt

class CandleList(object):
    '''
    Class that represents a list of candles

    Class variables
    ---------------
    clist : list, Required
            List of Candle objects
    instrument : str, Optional
                 Instrument for this CandleList (i.e. AUD_USD or EUR_USD etc...)
    granularity : str, Optional
                Granularity for this CandleList (i.e. D, H12, H8 etc...)
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

    def __init__(self, clist,instrument=None, granularity=None, type=None,seq=None, number_of_0s=None,
                 longest_stretch=None, highlow_double0s=None, 
                 openclose_double0s=None, entropy=None):
        self.clist=clist
        self.instrument=instrument
        self.granularity=granularity
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

    def fetch_by_time(self, datetime):
        '''
        Function to get a candle using its datetime

        Parameters
        ----------
        datetime    datetime object for candle that wants
                    to be fetched

        Returns
        -------
        Candle object
        '''

        d=datetime
        delta = None
        if self.granularity == "D":
            delta = timedelta(hours=24)
        else:
            fgran = self.granularity.replace('H', '')
            delta = timedelta(hours=int(fgran))

        sel_c=None

        for c in self.clist:
            start=c.time
            end=start+delta
            if d>=start and d < end:
                sel_c=c

        if sel_c is None: raise Exception("No candle was selected with time: {0}".format(datetime))
        return sel_c


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

    def calc_rsi(self, period, rsi_period=14):
        '''
        Calculate the RSI for a certain candle list

        Parameters
        ----------
        period : int
                 Number of days for which close price data will be fetched. The larger the
                 number of days the more accurate the ewm calculation will be, as the exponential
                 moving average calculated for each of the windows (of size=rsi_period) will be
                 directly affected by the previous windows in the series
        rsi_period : int
                     Number of candles used for calculating the RSI. Default=14

        Returns
        -------
        Nothing
        '''

        start_time=self.clist[0].time
        end_time=self.clist[-1].time

        period_delta = timedelta(days=period)
        start_calc_time = start_time - period_delta

        #fetch candle set from start_calc_time
        oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                         instrument=self.instrument,
                         granularity=self.granularity,
                         alignmentTimezone='Europe/London',
                         dailyAlignment=22)

        oanda.run(start=start_calc_time.isoformat(),
                  end=end_time.isoformat(),
                  roll=True)

        candle_list = oanda.fetch_candleset()

        series=[]
        series = [c.closeAsk for c in candle_list]

        df = pd.DataFrame({'close': series})
        chg = df['close'].diff(1)

        gain = chg.mask(chg < 0, 0)
        loss = chg.mask(chg > 0, 0)

        avg_gain = gain.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
        avg_loss = loss.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()

        rs = abs(avg_gain / avg_loss)

        rsi = 100 - (100 / (1 + rs))

        rsi4cl=rsi[-len(self.clist):]
        # set rsi attribute in each candle of the CandleList
        ix=0
        for c,v in zip(self.clist,rsi4cl):
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
        sorted from older to newer
        '''

        adj=False
        init=False
        num_times=0
        length=0
        lengths=[]

        for c in self.clist:
            if c.rsi is None: raise Exception("RSI values are not defined for this Candlelist, "
                                              "run calc_rsi first")
            if self.type is None: raise Exception("type is not defined for this Candlelist")

            if self.type=='long':
                if c.rsi > 70 and adj is False:
                    num_times += 1
                    length = 1
                    adj = True
                elif c.rsi > 70 and adj is True:
                    length += 1
                elif c.rsi < 70:
                    if adj is True: lengths.append(length)
                    adj = False
            elif self.type=='short':
                if c.rsi<30 and adj is False:
                    num_times+=1
                    length=1
                    adj=True
                elif c.rsi<30 and adj is True:
                    length+=1
                elif c.rsi>30:
                    if adj is True: lengths.append(length)
                    adj=False

        if adj is True and length>0: lengths.append(length)

        if num_times != len(lengths): raise Exception("Number of times" \
                                                      "and lengths do not" \
                                                      "match")
        return { 'number' : num_times,
                 'lengths' : lengths}

    def get_length_candles(self):
        '''
        Function to calculate the length of CandleList in number of candles

        Returns
        -------
        int Length in number of candles
        '''

        for i in self.clist:
            print(i.time)
        return len(self.clist)

    def get_length_pips(self, part='openAsk'):
        '''
        Function to calculate the length of CandleList in number of pips

        Parameters
        ----------
        part : str
               What part of the candle will be used for calculating the length in pips
               Possible values are: 'openAsk', 'closeAsk', 'lowAsk', 'openBid', 'closeBid'

        Returns
        -------
        int Length in number of pips
        '''


        start_cl=self.clist[0]
        end_cl=self.clist[-1]

        (first,second)=self.instrument.split("_")
        round_number=None
        if first=='JPY' or second=='JPY':
            round_number=2
        else:
            round_number=4

        start_price=round(getattr(start_cl,part),round_number)
        end_price=round(getattr(end_cl,part),round_number)

        diff=(start_price-end_price)*10**round_number

        return abs(int(round(diff,0)))

    def __get_bounces(self, data, direction):

        cb = np.array(data)

        ixs=None
        if direction=='up':
            ixs = peakutils.indexes(cb, thres=0.5, min_dist=5)
        elif direction=='down':
            ixs = peakutils.indexes(-cb, thres=0.5, min_dist=5)

        bounces = []
        for ix in ixs:
            bounces.append(data[ix])

        return bounces


    def fit_reg_line(self, part='openAsk', smooth='rolling_average', k_perc=25, outfile='regression_line.png'):
        '''
        Function to fit a linear regression
        line on candle list. This can be used in order to assess the direction of
        the trend (upward, downward)

        Parameters
        ----------
        part : str
               What part of the candle will be used for calculating the length in pips
               Possible values are: 'openAsk', 'closeAsk', 'lowAsk', 'openBid', 'closeBid'
               Default: openAsk
        smooth : str
                 What method will be used in order to smooth the data
                 Possible values are: 'rolling_average'
        k_perc : int
            % of CandleList length that will be used as window size used for calculating the rolling average.
            For example, if CandleList length = 20 Candles. Then the k=25% will be a window_size of 5
            Default: 25
        outfile : FILE
                  Path to output .png file that will show the fitted regression line

        Returns
        -------
        Fitted model, png_file, regression_model_mse
        '''

        prices=[]
        x=[]
        for i in range(len(self.clist)):
            x.append(i)
            prices.append(getattr(self.clist[i],part))

        model = LinearRegression(fit_intercept=True)

        if smooth=='rolling_average':
            k=int(abs((k_perc*len(self.clist)/100)))
            d = {'x': x, 'prices': prices}
            df = pd.DataFrame(data=d)
            df['prices_norm'] = df[['prices']].rolling(k).mean()
            df = df.dropna()
            prices=df['prices_norm']
            x=df['x']

        model.fit(np.array(x).reshape(-1,1), np.array(prices).reshape(-1,1))

        y_pred = model.predict(np.array(x).reshape(-1,1))

        # Evaluation of the model with MSE
        regression_model_mse = mean_squared_error(y_pred, np.array(prices).reshape(-1, 1))

        fig = plt.figure(figsize=(20, 10))
        plt.scatter(x, prices)
        plt.plot(x, y_pred, color='red')
        fig.savefig(outfile, format='png')

        return model, outfile, regression_model_mse

    def check_if_divergence(self,part='openAsk',direction='up'):
        '''
        Function to check if there is divergence between prices
        and RSI indicator

        Parameters
        ----------
        part : str
               What part of the candle to use for the calculation
               Default: 'openAsk'
        direction : str
                    Direction of the trend. Possible values are 'up'/'down'

        Returns
        -------
        bool True if there is divergence. "n.a." if the divergence was not calculated
        '''

        rsi_values=[]
        prices=[]
        for c in self.clist:
            if c.rsi is None: raise Exception("RSI values are not defined for this Candlelist, "
                                              "run calc_rsi first")
            prices.append(getattr(c, part))
            rsi_values.append(getattr(c, 'rsi'))

        bounces_prices=self.__get_bounces(prices,direction=direction)
        bounces_rsi = self.__get_bounces(rsi_values, direction=direction)

        if len(bounces_prices)<2 or len(bounces_rsi)<2:
            print("WARN: No enough bounces after the trend start were found. Divergence assessment will be skipped")
            return "n.a."

        diff_prices=bounces_prices[-1]-bounces_prices[-2]
        diff_rsi=bounces_rsi[-1]-bounces_rsi[-2]

        if np.sign(diff_prices) == np.sign(diff_rsi):
            return False
        else:
            return True

