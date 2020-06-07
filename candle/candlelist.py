from scipy import stats
from apis.oanda_api import OandaAPI
from zigzag import *
from pivot.pivotlist import PivotList
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from configparser import ConfigParser
from pandas.plotting import register_matplotlib_converters
from ast import literal_eval
register_matplotlib_converters()
import pandas as pd
import numpy as np
import matplotlib
import logging
from utils import *

matplotlib.use('PS')
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)

# create logger
cl_logger = logging.getLogger(__name__)


class CandleList(object):
    '''
    Class that represents a list of candles

    Class variables
    ---------------
    clist : list, Required
            List of Candle objects
    settingf : str, Optional
               Path to *.ini file with settings
    settings : ConfigParser object generated using 'settingf'
               Optional
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
    id : str, Optional
         Identifier for this CandleList (i.e. EUR_GBP 15MAY2007D)
    '''

    def __init__(self, clist, settingf=None, settings=None,
                 instrument=None, granularity=None,
                 type=None, seq=None, number_of_0s=None,
                 longest_stretch=None, highlow_double0s=None,
                 openclose_double0s=None, entropy=None, id=None):
        self.clist = clist
        self.settingf = settingf
        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings

        # set type if not defined depending on
        # the price diff betweeen clist[0] and clist[-1]
        if type is None:
            price_1st = getattr(clist[0], self.settings.get('general', 'part'))
            price_last = getattr(clist[-1], self.settings.get('general', 'part'))
            if price_1st > price_last:
                self.type = 'short'
            elif price_1st < price_last:
                self.type = 'long'
        else:
            self.type = type

        self.instrument = instrument
        self.granularity = granularity
        self.len = len(clist)
        self.seq = seq
        self.number_of_0s = number_of_0s
        self.longest_stretch = longest_stretch
        self.highlow_double0s = highlow_double0s
        self.openclose_double0s = openclose_double0s
        self.entropy = entropy
        self.id = id
        self.ix = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.ix < self.len:
            candle = self.clist[self.ix]
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

    def fetch_by_time(self, adatetime, period=0):
        '''
        Function to get a candle using its datetime

        Parameters
        ----------
        adatetime:   datetime object for candle that wants
                    to be fetched
        period: int
                Number of candles above/below 'adatetime' that will be fetched

        Returns
        -------
        Candle object
        '''

        d=adatetime
        delta = None
        delta_period = None

        if self.granularity == "D":
            delta = timedelta(hours=24)
            delta_period = timedelta(hours=24*period)
        else:
            fgran = self.granularity.replace('H', '')
            delta = timedelta(hours=int(fgran))
            delta_period = timedelta(hours=int(fgran)*period)

        if period == 0:
            sel_c = None
            for c in self.clist:
                start = c.time
                end = start+delta
                if d >= start and d < end:
                    sel_c = c

            if sel_c is None:
                raise Exception("No candle was selected with time: {0}\n."
                                " It is good to check if the marked is closed".format(datetime))
            return sel_c
        elif period > 0:
            start = d-delta_period
            end = d+delta_period
            sel_c = []
            for c in self.clist:
                if c.time >= start and c.time <= end:
                    sel_c.append(c)
            if len(sel_c) == 0: raise Exception("No candle was selected"
                                                " for range: {0}-{1}".format(start, end))
            return sel_c

    def __get_number_of_double0s(self, seq1, seq2, norm=True):
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
        list1 = list(seq1)
        list2 = list(seq2)

        if len(list1) != len(list2):
            raise Exception("Lengths of seq1 and seq2 are not equal")

        number_of_double0s = 0
        for i, j in zip(list1, list2):
            if i is "N" or j is "N":
                print("Skipping this column as there is a N in the binary seq")
                continue
            if int(i) == 0 and int(j) == 0:
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

        high_low = self.__get_number_of_double0s(self.seq['high'], self.seq['low'], norm=norm)
        open_close = self.__get_number_of_double0s(self.seq['open'], self.seq['close'], norm=norm)
        
        self.highlow_double0s = high_low
        self.openclose_double0s = open_close
        
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
        '''
        cl_logger.debug("Running calc_rsi")

        start_time = self.clist[0].time
        end_time = self.clist[-1].time

        delta_period = None
        if self.granularity == "D":
            delta_period = timedelta(hours=24 * self.settings.getint('candlelist', 'period'))
        else:
            fgran = self.granularity.replace('H', '')
            delta_period = timedelta(hours=int(fgran) * self.settings.getint('candlelist', 'period'))

        start_calc_time = start_time - delta_period

        #fetch candle set from start_calc_time
        oanda = OandaAPI(instrument=self.instrument,
                         granularity=self.granularity,
                         settingf=self.settingf,
                         settings=self.settings)
        '''
        Get candlelist from start_calc_time to (start_time-1)
        This 2-step API call is necessary in order to avoid
        maximum number of candles errors
        '''
        oanda.run(start=start_calc_time.isoformat(),
                  end=start_time.isoformat())

        cl1 = oanda.fetch_candleset()

        '''Get candlelist from start_time to end_time'''
        oanda.run(start=start_time.isoformat(),
                  end=end_time.isoformat())

        cl2 = oanda.fetch_candleset()

        if cl1[-1].time == cl2[0].time:
            del cl1[-1]

        candle_list = cl1 + cl2

        series = [c.closeAsk for c in candle_list]

        df = pd.DataFrame({'close': series})
        chg = df['close'].diff(1)

        gain = chg.mask(chg < 0, 0)
        loss = chg.mask(chg > 0, 0)

        rsi_period = self.settings.getint('candlelist', 'rsi_period')
        avg_gain = gain.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
        avg_loss = loss.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()

        rs = abs(avg_gain / avg_loss)

        rsi = 100 - (100 / (1 + rs))

        rsi4cl = rsi[-len(self.clist):]
        # set rsi attribute in each candle of the CandleList
        ix = 0
        for c, v in zip(self.clist, rsi4cl):
            self.clist[ix].rsi = round(v, 2)
            ix += 1

        cl_logger.debug("Done calc_rsi")

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
        num_times=0
        length=0
        lengths=[]

        for c in self.clist:
            if c.rsi is None:
                raise Exception("RSI values are not defined for this Candlelist, "
                                "run calc_rsi first")
            if self.type is None:
                raise Exception("type is not defined for this Candlelist")

            if self.type == 'short':
                if c.rsi > 70 and adj is False:
                    num_times += 1
                    length = 1
                    adj = True
                elif c.rsi > 70 and adj is True:
                    length += 1
                elif c.rsi < 70:
                    if adj is True: lengths.append(length)
                    adj = False
            elif self.type=='long':
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

        return len(self.clist)

    def get_length_pips(self):
        '''
        Function to calculate the length of CandleList in number of pips

        Returns
        -------
        int Length in number of pips
        '''


        start_cl = self.clist[0]
        end_cl = self.clist[-1]

        (first, second) = self.instrument.split("_")
        round_number = None
        if first == 'JPY' or second == 'JPY':
            round_number = 2
        else:
            round_number = 4

        start_price = round(getattr(start_cl, self.settings.get('general', 'part')), round_number)
        end_price = round(getattr(end_cl, self.settings.get('general', 'part')), round_number)

        diff = (start_price-end_price)*10**round_number

        return abs(int(round(diff, 0)))

    def fit_reg_line(self, smooth='rolling_average', k_perc=25):
        '''
        Function to fit a linear regression line on candle list.
        This can be used in order to assess the direction of the trend (upwards, downwards)

        Parameters
        ----------
        smooth : str
                 What method will be used in order to smooth the data
                 Possible values are: 'rolling_average'
        k_perc : int
            % of CandleList length that will be used as window size used for calculating the rolling average.
            For example, if CandleList length = 20 Candles. Then the k=25% will be a window_size of 5
            Default: 25

        Returns
        -------
        Fitted model, regression_model_mse
        '''

        prices = []
        x = []
        for i in range(len(self.clist)):
            x.append(i)
            prices.append(getattr(self.clist[i], self.settings.get('general', 'part')))

        model = LinearRegression(fit_intercept=True)

        if smooth == 'rolling_average':
            k = int(abs((k_perc*len(self.clist)/100)))
            d = {'x': x, 'prices': prices}
            df = pd.DataFrame(data=d)
            df['prices_norm'] = df[['prices']].rolling(k).mean()
            df = df.dropna()
            prices = df['prices_norm']
            x = df['x']

        model.fit(np.array(x).reshape(-1, 1), np.array(prices).reshape(-1, 1))

        y_pred = model.predict(np.array(x).reshape(-1, 1))

        # Evaluation of the model with MSE
        regression_model_mse = mean_squared_error(y_pred, np.array(prices).reshape(-1, 1))

        # generate output file with fitted regression line
        # parse string from parser object into a tuple
        figsize = literal_eval(self.settings.get('images', 'size'))
        fig = plt.figure(figsize=figsize)
        plt.scatter(x, prices)
        plt.plot(x, y_pred, color='red')

        outfile = "{0}/fitted_line/{1}.fitted.png".format(self.settings.get('images', 'outdir'),
                                                          self.id.replace(' ', '_'))
        fig.savefig(outfile, format='png')

        return model, regression_model_mse

    def get_pivotlist(self, th_bounces, outfile=None):
        '''
        Function to obtain a pivotlist object containing pivots identified using the
        Zigzag indicator.
        It will also generate a .png image of the identified pivots

        Parameter
        ---------
        th_bounces: float
                    Value used by ZigZag to identify pivots. The lower the
                    value the higher the sensitivity
        outfile: str
                 .png file for saving the plot with pivots.
                 Optional

        Return
        ------
        PivotList object
        '''

        cl_logger.debug("Running get_pivotlist")

        x = []
        values = []
        for i in range(len(self.clist)):
            x.append(i)
            values.append(getattr(self.clist[i],
                                  self.settings.get('general', 'part')))

        xarr = np.array(x)
        yarr = np.array(values)

        pivots = peak_valley_pivots(yarr, th_bounces,
                                    th_bounces*-1)

        pl = PivotList(parray=pivots,
                       clist=self,
                       settingf=self.settingf,
                       settings=self.settings)

        if self.settings.getboolean('pivots', 'plot') is True:
            if outfile is None:
                outfile = "{0}/pivots/{1}.allpivots.png".format(self.settings.get('images', 'outdir'),
                                                                self.id.replace(' ', '_'))
            figsize = literal_eval(self.settings.get('images', 'size'))
            fig = plt.figure(figsize=figsize)
            plt.plot(xarr, yarr, 'k:', alpha=0.5)
            plt.plot(xarr[pivots != 0], yarr[pivots != 0], 'k-')
            plt.scatter(xarr[pivots == 1], yarr[pivots == 1], color='g')
            plt.scatter(xarr[pivots == -1], yarr[pivots == -1], color='r')

            fig.savefig(outfile, format='png')

        cl_logger.debug("Done get_pivotlist")

        return pl

    def check_if_divergence(self, number_of_bounces=3):
        '''
        Function to check if there is divergence between prices
        and RSI indicator

        Parameters
        ----------
        number_of_bounces : int
                            Number of rsi bounces from last (most recent)
                            to consider for calculating divergence. Default=3

        Returns
        -------
        bool True if there is divergence. "n.a." if the divergence was not calculated
        '''

        outfile_rsi="{0}/{1}.rsi.png".format(config.PNGFILES['div'],
                                             self.id.replace(' ', '_'))

        plist = self.get_pivotlist(outfile=outfile_rsi, part="rsi", th_up=0.1, th_down=-0.1)

        bounce_rsi=plist.plist

        arr = np.array(self.clist)

        # consider type of trade in order to select peaks or valleys
        bounce_rsiA=None
        if self.type == 'short':
            bounce_rsiA = arr[bounce_rsi == 1]
        elif self.type == 'long':
            bounce_rsiA = arr[bounce_rsi == -1]

        #consider only the  desired number_of_bounces
        candles_rsi = bounce_rsiA[-number_of_bounces:]

        if len(candles_rsi)<2:
            print("WARN: No enough bounces after the trend start were found. Divergence assessment will be skipped")
            return "n.a."

        cl = CandleList(candles_rsi,
                        instrument=self.instrument,
                        granularity=self.granularity,
                        id=self.id,
                        type=self.type)

        # fit a regression line for rsi bounces
        outfile_rsi = "{0}/{1}.reg_rsi.png".format(config.PNGFILES['div'],
                                               self.id.replace(' ', '_'))
        (model_rsi, regression_model_mse_rsi)=cl.fit_reg_line(outfile=outfile_rsi, part='rsi', smooth=None )

        # fit a regression line for price bounces
        outfile_price = "{0}/{1}.reg_price.png".format(config.PNGFILES['div'],
                                                       self.id.replace(' ', '_'))
        (model_price, regression_model_mse_price) = cl.fit_reg_line(outfile=outfile_price, part=part, smooth=None)


        # check if sign of slope is different between rsi and price lines
        if np.sign(model_rsi.coef_[0, 0])!= np.sign(model_price.coef_[0, 0]):
            return True
        else:
            return False

    def slice(self, start=None, end=None):
        '''
        Function to slice self on a date interval. It will return the sliced CandleList

        Parameters
        ----------
        start: datetime
               Slice the CandleList from this start datetime. It will create a new CandleList starting
               from this datetime. If 'end' is not defined, then it will slice the CandleList from 'start'
               to the end of the CandleList
               Optional
        end: datetime. If 'start' is not defined, then it will slice from beginning of CandleList to 'end'
             Optional

        Returns
        -------
        CandleList object

        Raises
        ------
        Exception
            If start > end
        '''
        sliced_clist = []
        if start is not None and end is None:
            sliced_clist = [c for c in self.clist if c.time >= start]
        elif start is not None and end is not None:
            if start > end:
                raise Exception("Start is greater than end. Can't slice this CandleList")
            sliced_clist = [c for c in self.clist if c.time >= start and c.time <= end]
        elif start is None and end is not None:
            sliced_clist = [c for c in self.clist if c.time <= end]

        cl = CandleList(sliced_clist,
                        instrument=self.instrument,
                        granularity=self.granularity,
                        id=self.id,
                        type=self.type,
                        settingf=self.settingf,
                        settings=self.settings)

        return cl

    def improve_resolution(self, price, min_dist, part='closeAsk'):
        '''
        Function used to improve the resolution of the identified maxima/minima. This function will select
        the candle closer to 'price' when there are 2 candles less than 'min_dist' apart

        Parameters
        ----------
        price : float
                Price that will be used as the reference to select one of the candles
        min_dist : int
                   minimum distance between the identified max/min. Required
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        list containing the selected candles
        '''

        min_distDelta=None
        if min_dist is not None:
            # convert the min_dist integer to a timedelta
            min_distDelta = periodToDelta(ncandles=min_dist,
                                          timeframe=self.granularity)

        list_c=self.clist
        res = [x.time - y.time for x, y in zip(list_c, list_c[1:])]
        below = []  # below will contain the list_c indexes separated by <min_dist
        ix = 0
        for i in res:
            i = abs(i)
            if min_distDelta is not None:
                if i < min_distDelta:
                    below.append((ix, ix + 1))
            else:
                below.append((ix,ix+1))
            ix += 1

        remove_l = [] #list with the indexes to remove
        if below:
            for i in below:
                x0 = getattr(list_c[i[0]], part)
                x1 = getattr(list_c[i[1]], part)
                diff0=abs(x0-price)
                diff1=abs(x1-price)
                #ix to be removed: the furthest
                # from self.price
                if diff0>diff1:
                    remove_l.append(i[0])
                elif diff1>diff0:
                    remove_l.append(i[1])
                elif diff1==diff0:
                    remove_l.append(i[0])

        if remove_l:
            sorted_removel=sorted(list(set(remove_l)))
            list_c = [i for j, i in enumerate(list_c) if j not in sorted_removel]

        return list_c

    def calc_itrend(self):
        '''
        Function to calculate the datetime for the start of this CandleList, assuming that this
        CandleList is trending. This function will calculate the start of the trend by using the self.get_pivots
        function

        Returns
        -------
        Merged segment containing the trend_i
        '''

        cl_logger.debug("Running calc_itrend")

        outfile = "{0}/pivots/{1}.calc_it.allpivots.png".format(self.settings.get('images', 'outdir'),
                                                                self.id.replace(' ', '_'))

        pivots = self.get_pivotlist(th_bounces=self.settings.getfloat('it_trend', 'th_bounces'),
                                    outfile=outfile)

        # merge segments
        for p in reversed(pivots.plist):
            adj_t = p.adjust_pivottime(clistO=pivots.clist)
            # get new CandleList with new adjusted time for the end
            newclist = pivots.clist.slice(start=pivots.clist.clist[0].time,
                                          end=adj_t)
            newp = newclist.get_pivotlist(self.settings.getfloat('it_trend', 'th_bounces')).plist[-1]
            newp.merge_pre(slist=pivots.slist,
                           n_candles=self.settings.getint('it_trend', 'n_candles'),
                           diff_th=self.settings.getint('it_trend', 'diff_th'))
            return newp.pre

        cl_logger.debug("Done clac_itrend")

    def get_lasttime(self, hrarea):
        '''
        Function to get the datetime for last time that price has been above/below a HArea

        Parameters
        ----------
        hrarea : HArea object used to calculate the lasttime

        Returns
        -------
        Will return the last time the price was above/below the self.SR.
        Price is considered to be above (for short trades) the self.SR when candle's lowAsk is
        above self.SR.upper and considered to be below (for long trades) the self.SR when candle's
        highAsk is below sel.SR.below.

        Returned datetime will be the datetime for the first candle in self.clist
        if last time was not found
        '''

        if self.type == "short":
            position = 'above'
        if self.type == "long":
            position = 'below'

        last_time = hrarea.last_time(clist=self.clist,
                                     position=position)

        # if last_time is not defined in this CandleList then assign the time for the first candle
        if last_time is None:
            last_time = self.clist[0].time

        return last_time

    def get_highest(self):
        '''
        Function to calculate the highest
        price in this CandeList

        Returns
        -------
        Float representing highest price
        '''

        max = 0.0
        for c in self.clist:
            price = getattr(c, self.settings.get('general', 'part'))
            if price > max:
                max = price

        return max

    def get_lowest(self):
        '''
        Function to calculate the lowest
        price in this CandeList

        Returns
        -------
        Float representing lowest price
        '''

        min = None
        for c in self.clist:
            price = getattr(c, self.settings.get('general', 'part'))
            if min is None:
                min = price
            else:
                if price < min:
                    min = price
        return min