import datetime
import re
import pdb
from datetime import datetime,timedelta


def try_parsing_date(text):
    '''
    Function to parse a string that can be formatted in
    different datetime formats

    :returns
    datetime object
    '''

    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')

def calculate_pips(pair, price):
    '''
    Function to calculate the number of pips
    for a given price

    Parameters
    ----------
    pair : str, Required
           Currency pair used in the trade. i.e. AUD_USD
    price : float

    Returns
    -------
    float
          Number of pips
    '''

    pips = None
    (first, second) = pair.split("_")
    if first == 'JPY' or second == 'JPY':
        pips = price * 100
    else:
        pips = price * 10000

    return '%.1f' % pips

def add_pips2price(pair, price, pips):
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
               Timeframe used for getting the delta object. Possible values are: 2D,D,H12,H10,H8,H4

    Returns
    -------
    datetime timedelta object
    '''

    patt=re.compile("(\d)D")

    delta = None
    if patt.match(timeframe):
        raise Exception("{0} is not valid. Oanda rest service does not take it".format(timeframe))
    elif timeframe=='D':
        delta = timedelta(hours=24 * ncandles)
    else:
        fgran = timeframe.replace('H', '')
        delta = timedelta(hours=int(fgran) * ncandles)

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

def correct_timeframe(settings, timeframe):
    """
    This utility function is used for correcting
    all the pips-related settings depending
    on the selected timeframe

    Parameters
    ----------
    settings: ConfigParser object
    timeframe : D,H12,H8,4

    Returns
    -------
    settings : ConfigParser object timeframe corrected
    """
    timeframe = int(timeframe.replace('H', ''))
    ratio = round(timeframe/24, 2)

    p = re.compile('.*pips')

    for section_name in settings.sections():
        for key, value in settings.items(section_name):
            if section_name == 'trade' and key == 'hr_pips':
                continue
            if p.match(key):
                new_pips = int(round(ratio*int(value), 0))
                settings.set(section_name, key, str(new_pips))

    return settings
