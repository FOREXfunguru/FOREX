import numpy as np
import pdb
import matplotlib
import operator
matplotlib.use('PS')
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.signal import argrelextrema


class HArea(object):
    '''
    Class to represent a horizontal area in the chart

    Class variables
    ---------------
    price : float, Required
            Price in the chart used as the middle point that will be extended on both sides a certain
            number of pips
    pips : float, Required
          Number of pips to extend on each side
    instrument : str, Optional
                 Instrument for this CandleList (i.e. AUD_USD or EUR_USD etc...)
    granularity : str, Optional
                Granularity for this CandleList (i.e. D, H12, H8 etc...)
    upper : float, Optional
           Upper limit of area
    lower : float, Optional
            Lower limit of area
    '''

    def __init__(self, price, pips, instrument, granularity):

        (first, second) = instrument.split("_")
        self.instrument=instrument
        round_number = None
        divisor = None
        if first == 'JPY' or second == 'JPY':
            round_number = 2
            divisor=100
        else:
            round_number = 4
            divisor=10000
        price = round(price, round_number)
        self.price = price
        self.pips = pips
        self.granularity = granularity
        self.upper=price+(pips/divisor)
        self.lower=price-(pips/divisor)

    def number_bounces(self, datetimes, prices, smooth=False, outfile='bounces.png'):
        '''
        Function used to calculate the datetime for previous bounces in this area

        Parameters
        ----------
        datetimes : list
                    Lisf of datetimes associated to each of the prices
        prices : list
                 List of prices used to calculate the bounces
        smooth : bool
                 Smooth the numerical data using savitzky_folay
        outfile : file
                  Filename for output

        Returns
        -------
        file : png file with identified bounces
        '''

        data=None
        if smooth is True:
            data=savgol_filter(prices, 31, 3)
        else:
            data=np.array(prices)

        # for local maxima
        max = argrelextrema(data, np.greater)
        min = argrelextrema(data, np.less)

        fig = plt.figure(figsize=(20, 10))
        ax = plt.axes()
        ax.plot(datetimes, data,color="black")

        bounces=[]
        for ix in max[0]:
            if data[ix]>=self.lower and data[ix]<=self.upper:
                bounces.append((datetimes[ix],data[ix]))
                plt.scatter(datetimes[ix], data[ix], s=50)

        for ix in min[0]:
            if data[ix] <= self.upper and data[ix] >= self.lower:
                bounces.append((datetimes[ix], data[ix]))
                plt.scatter(datetimes[ix], data[ix], s=50)

        fig.savefig(outfile, format='png')

        pr_date=None
        f_bounces=[]
        bounces.sort(key=operator.itemgetter(0))
        for d in bounces:
            if pr_date is None:
                f_bounces.append(d)
                pr_date=d[0]
                continue
            else:
                diff=d[0]-pr_date
                hours=diff.days*24
                hr_divisor=None
                if self.granularity=='D':
                    hr_divisor=24
                else:
                    hr_divisor=int(self.granularity.replace('H',''))
                number_of_candles=hours/hr_divisor
                if number_of_candles<=10:
                    pr_date = d[0]
                    continue
                else:
                    f_bounces.append(d)
                pr_date=d[0]

        fig = plt.figure(figsize=(20, 10))
        ax = plt.axes()
        ax.plot(datetimes, data, color="blue")
        for d in f_bounces:
            plt.scatter(d[0], d[1], s=50)

        fig.savefig(outfile+"filt.png", format='png')
        pdb.set_trace()
        return f_bounces
