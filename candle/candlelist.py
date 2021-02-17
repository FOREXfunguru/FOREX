from oanda.connect import Connect
from zigzag import *
from pivot_list import PivotList
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from pandas.plotting import register_matplotlib_converters
from ast import literal_eval
register_matplotlib_converters()
import pandas as pd
import numpy as np
import matplotlib
import logging
from utils import *

from config import CONFIG
matplotlib.use('PS')
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)

# create logger
cl_logger = logging.getLogger(__name__)
cl_logger.setLevel(logging.INFO)

class CandleList(object):
    '''
    Container for the FOREX data that is passed through the data class variable
    as a dict with the following format:

    {'instrument' : 'AUD_USD',
     'granularity' : 'D',
     'candles' : [{...},{...}]}

     The value for the key named 'candles' in the dictionary will be a list of dicts,
     where each of the dicts is a single candle

    Class variables
    ---------------
    data : dict containing the FOREX data, Required
    type : str, Optional
           Type of this CandleList. Possible values are 'long'/'short'
    '''

    def __init__(self, data, type=None):
        # Transforming all datetime strs to datetime objects
        for c in data['candles']:
            if isinstance(c['time'], datetime):
                continue
            else:
                c['time'] = datetime.strptime(c['time'], '%Y-%m-%dT%H:%M:%S.%fZ')

        self.data = data

        # set type if not defined depending on
        # the price diff betweeen self.data['candles'][0] and self.data['candles'][-1]
        if type is None:
            price_1st = self.data['candles'][0][CONFIG.get('general', 'part')]
            price_last = self.data['candles'][-1][CONFIG.get('general', 'part')]
            if price_1st > price_last:
                self.type = 'short'
            elif price_1st < price_last:
                self.type = 'long'
        else:
            self.type = type

    def fetch_by_time(self, adatetime, period=0):
        '''
        Function to get a candle using its datetime

        Parameters
        ----------
        adatetime: datetime object for candle that wants
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

        if self.data['granularity'] == "D":
            delta = timedelta(hours=24)
            delta_period = timedelta(hours=24*period)
        else:
            fgran = self.data['granularity'].replace('H', '')
            delta = timedelta(hours=int(fgran))
            delta_period = timedelta(hours=int(fgran)*period)

        if period == 0:
            sel_c = None
            for c in self.data['candles']:
                start = c['time']
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
            for c in self.data['candles']:
                if c['time'] >= start and c['time'] <= end:
                    sel_c.append(c)
            if len(sel_c) == 0: raise Exception("No candle was selected"
                                                " for range: {0}-{1}".format(start, end))
            return sel_c

    def calc_rsi(self):
        '''
        Calculate the RSI for a certain candle list
        '''
        cl_logger.debug("Running calc_rsi")

        start_time = self.data['candles'][0]['time']
        end_time = self.data['candles'][-1]['time']

        delta_period = None
        if self.data['granularity'] == "D":
            delta_period = timedelta(hours=24 * CONFIG.getint('candlelist', 'period'))
        else:
            fgran = self.data['granularity'].replace('H', '')
            delta_period = timedelta(hours=int(fgran) * CONFIG.getint('candlelist', 'period'))

        start_calc_time = start_time - delta_period

        #fetch candles from start_calc_time
        conn = Connect(instrument=self.data['instrument'],
                       granularity=self.data['granularity'])
        '''
        Get candlelist from start_calc_time to (start_time-1)
        This 2-step API call is necessary in order to avoid
        maximum number of candles errors
        '''
        ser_dir = None
        if CONFIG.has_option('general', 'ser_data_dir'):
            ser_dir = CONFIG.get('general', 'ser_data_dir')

        cl_logger.debug("Fetching data from API")
        cl1_res = conn.query(start=start_calc_time.isoformat(),
                             end=start_time.isoformat(),
                             indir=ser_dir)

        '''Get candlelist from start_time to end_time'''
        cl2_res = conn.query(start=start_time.isoformat(),
                             end=end_time.isoformat(),
                             indir=ser_dir)

        if cl1_res['candles'][-1]['time'] == cl2_res['candles'][0]['time']:
            del cl1_res['candles'][-1]

        candle_list = cl1_res['candles'] + cl2_res['candles']

        series = [c['closeAsk'] for c in candle_list]

        df = pd.DataFrame({'close': series})
        chg = df['close'].diff(1)

        gain = chg.mask(chg < 0, 0)
        loss = chg.mask(chg > 0, 0)

        rsi_period = CONFIG.getint('candlelist', 'rsi_period')
        avg_gain = gain.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
        avg_loss = loss.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()

        rs = abs(avg_gain / avg_loss)

        rsi = 100 - (100 / (1 + rs))

        rsi4cl = rsi[-len(self.data['candles']):]
        # set rsi attribute in each candle of the CandleList
        ix = 0
        for c, v in zip(self.data['candles'], rsi4cl):
            self.data['candles'][ix]['rsi'] = round(v, 2)
            ix += 1

        cl_logger.debug("Done calc_rsi")

    def calc_rsi_bounces(self):
        '''
        Calculate the number of times that the
        price has been in overbought (>70) or
        oversold (<30) regions

        Returns
        -------
        dict:
             {number: 3
             lengths: [4,5,6]}
        Where number is the number of times price
        has been in overbought/oversold and lengths list
        is formed by the number of candles that the price
        has been in overbought/oversold each of the times
        sorted from older to newer
        '''

        adj = False
        num_times = 0
        length = 0
        lengths = []

        for c in self.data['candles']:
            if c['rsi'] is None:
                raise Exception("RSI values are not defined for this Candlelist, "
                                "run calc_rsi first")
            if self.type is None:
                raise Exception("type is not defined for this Candlelist")

            if self.type == 'short':
                if c['rsi'] > 70 and adj is False:
                    num_times += 1
                    length = 1
                    adj = True
                elif c['rsi'] > 70 and adj is True:
                    length += 1
                elif c['rsi'] < 70:
                    if adj is True: lengths.append(length)
                    adj = False
            elif self.type == 'long':
                if c['rsi']<30 and adj is False:
                    num_times += 1
                    length = 1
                    adj=True
                elif c['rsi'] < 30 and adj is True:
                    length += 1
                elif c['rsi'] > 30:
                    if adj is True: lengths.append(length)
                    adj = False

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
        return len(self.data['candles'])

    def get_length_pips(self):
        '''
        Function to calculate the length of CandleList in number of pips

        Returns
        -------
        int Length in number of pips
        '''

        start_cl = self.data['candles'][0]
        end_cl = self.data['candles'][-1]

        (first, second) = self.data['instrument'].split("_")
        round_number = None
        if first == 'JPY' or second == 'JPY':
            round_number = 2
        else:
            round_number = 4

        start_price = round(start_cl[CONFIG.get('general', 'part')], round_number)
        end_price = round(end_cl[CONFIG.get('general', 'part')], round_number)

        diff = (start_price-end_price)*10**round_number

        return abs(int(round(diff, 0)))

    def fit_reg_line(self, outdir, smooth='rolling_average', k_perc=25):
        '''
        Function to fit a linear regression line on candle list.
        This can be used in order to assess the direction of the trend (upwards, downwards)

        Parameters
        ----------
        outdir : str
                 Directory for output files
        smooth : str
                 What method will be used in order to smooth the data
                 Possible values are: 'rolling_average'. Default: 'rolling_average'
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
        for i in range(len(self.data['candles'])):
            x.append(i)
            prices.append(self.data['candles'][i][CONFIG.get('general', 'part')])

        model = LinearRegression(fit_intercept=True)

        if smooth == 'rolling_average':
            k = int(abs((k_perc*len(self.data['candles'])/100)))
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
        if CONFIG.getboolean('images', 'plot') is True:
            figsize = literal_eval(CONFIG.get('images', 'size'))
            fig = plt.figure(figsize=figsize)
            plt.scatter(x, prices)
            plt.plot(x, y_pred, color='red')
            outfile = "{0}/fitted_line/{1}.fitted.png".format(outdir,
                                                              self.data['instrument'])
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
        for i in range(len(self.data['candles'])):
            x.append(i)
            values.append(self.data['candles'][i][CONFIG.get('general', 'part')])

        xarr = np.array(x)
        yarr = np.array(values)

        pivots = peak_valley_pivots(yarr, th_bounces,
                                    th_bounces*-1)
        pl = PivotList(parray=pivots,
                       clist=self)

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
            sliced_clist = [c for c in self.data['candles'] if c['time'] >= start]
        elif start is not None and end is not None:
            if start > end:
                raise Exception("Start is greater than end. Can't slice this CandleList")
            sliced_clist = [c for c in self.data['candles'] if c['time'] >= start and c['time'] <= end]
        elif start is None and end is not None:
            sliced_clist = [c for c in self['candles'] if c['time'] <= end ]
        new_dict = {}
        new_dict['candles'] = sliced_clist
        new_dict['instrument'] = self.data['instrument']
        new_dict['granularity'] = self.data['granularity']

        cl = CandleList(new_dict,
                        type=self.type)

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
        outfile = "{0}/pivots/{1}.calc_it.allpivots.png".format(CONFIG.get('images', 'outdir'),
                                                                self.data['instrument'].replace(' ', '_'))

        pivots = self.get_pivotlist(th_bounces=CONFIG.getfloat('it_trend', 'th_bounces'),
                                    outfile=outfile)

        # merge segments
        for p in reversed(pivots.plist):
            adj_t = p.adjust_pivottime(clistO=pivots.clist)
            # get new CandleList with new adjusted time for the end
            start = pivots.clist.data['candles'][0]['time']
            newclist = pivots.clist.slice(start= start,
                                          end=adj_t)
            newp = newclist.get_pivotlist(CONFIG.getfloat('it_trend', 'th_bounces')).plist[-1]
            newp.merge_pre(slist=pivots.slist,
                           n_candles=CONFIG.getint('it_trend', 'n_candles'),
                           diff_th=CONFIG.getint('it_trend', 'diff_th'))
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

        last_time = hrarea.last_time(clist=self.data['candles'],
                                     position=position)

        # if last_time is not defined in this CandleList then assign the time for the first candle
        if last_time is None:
            last_time = self.data['candles'][0]['time']

        return last_time

    def get_highest(self):
        '''
        Function to calculate the highest
        price in this CandleList

        Returns
        -------
        Float representing highest price
        '''

        max = 0.0
        for c in self.data['candles']:
            price = c[CONFIG.get('general', 'part')]
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
        for c in self.data['candles']:
            price = c[CONFIG.get('general', 'part')]
            if min is None:
                min = price
            else:
                if price < min:
                    min = price
        return min