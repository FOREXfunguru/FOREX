import datetime
import pdb

def calculate_pips(pair, price, decimals=1):
    '''
    Function to calculate the number of pips
    for a given price

    Parameters
    ----------
    pair : str, Required
           Currency pair used in the trade. i.e. AUD_USD
    price : float
    decimals : int
               Number of decimals for the returned number of
               pips. Default : 1

    Returns
    -------
    float
          Number of pips
    '''

    pips=None
    (first, second) = pair.split("_")
    if first == 'JPY' or second == 'JPY':
        pips = price * 100
    else:
        pips = price * 10000

    return '%.1f' % pips

def add_pips2price(pair,price,pips):
    '''
    Function that gets a price value and adds
    a certain number of pips to the price

    Parameters
    ----------
    pair : str, Required
           Currency pair used in the trade. i.e. AUD_USD
    price : float
    pips : int
           Number of pips to increase

    Returns
    -------
    float value
    '''

    (first, second) = pair.split("_")
    round_number = None
    divisor = None
    if first == 'JPY' or second == 'JPY':
        round_number = 2
        divisor = 100
    else:
        round_number = 4
        divisor = 10000
    price = round(price, round_number)

    iprice = price + (pips / divisor)

    return iprice

def substract_pips2price(pair, price, pips):
    '''
    Function that gets a price value and substracts
    a certain number of pips to the price

    Parameters
    ----------
    pair : str, Required
           Currency pair used in the trade. i.e. AUD_USD
    price : float
    pips : int
           Number of pips to decrease

    Returns
    -------
    float value
    '''

    (first, second) = pair.split("_")
    round_number = None
    divisor = None
    if first == 'JPY' or second == 'JPY':
        round_number = 2
        divisor = 100
    else:
        round_number = 4
        divisor = 10000
    price = round(price, round_number)

    dprice = price - (pips / divisor)

    return dprice

def periodToDelta(ncandles, timeframe):
    '''
    Function that receives an int representing a number of candles using the 'ncandles' param
    and returns a datetime timedelta object

    Parameters
    ----------
    ncandles: Number of candles for which the timedelta will be retrieved. Required
    timeframe: str, Required
               Timeframe used for getting the delta object. Possible values are: D,H12,H10,H8,H4

    Returns
    -------
    datetime timedelta object
    '''

    delta = None
    if timeframe == "D":
        delta = datetime.timedelta(hours=24 * ncandles)
    else:
        fgran = timeframe.replace('H', '')
        delta = datetime.timedelta(hours=int(fgran) * ncandles)

    return delta

def get_ixfromdatetimes_list(datetimes_list, d):
    '''
    Function to get the index of the element that is closest
    to the passed datetime

    Parameters
    ----------
    datetimes_list : list
                     List with datetimes
    d : datetime

    Returns
    -------
    int with index of the closest datetime to d
    '''

    sel_ix=None
    diff=None
    ix=0
    for ad in datetimes_list:
        if diff is None:
            diff=abs(ad-d)
            sel_ix=ix
        else:
            if abs(ad-d)<diff:
                sel_ix=ix
                diff=abs(ad-d)
        ix+=1

    return sel_ix

def pairwise(iterable):
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return zip(a, a)

