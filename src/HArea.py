import numpy as np
import pdb

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
    upper : float, Optional
           Upper limit of area
    lower : float, Optional
            Lower limit of area
    '''

    def __init__(self, price, pips):
        pdb.set_trace()
        price=round(price,4)
        self.price = price
        self.pips = pips
        self.upper=price+(pips/10000)
        self.lower=price-(pips/10000)

    def number_bounces(self, prices):
        '''
        Function used to calculate the datetime for previous bounces in this area

        Parameters
        ----------
        prices : list
                 List of prices used to calculate the bounces

        Returns
        -------

        '''
        data = -0.1 * np.cos(12 * np.array(prices)) + np.exp(-(1 - np.array(prices) ** 2))

