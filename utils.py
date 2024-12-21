import re
import os
import yaml
from typing import Tuple

from datetime import datetime, timedelta

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# location of directory used to store all data used by Unit Tests
DATA_DIR = ROOT_DIR+"/tests/data"


def try_parsing_date(date_string) -> datetime:
    """Function to parse a string that can be formatted in
    different datetime formats

    Returns:
        datetime object
    """
    if isinstance(date_string, datetime):
        return date_string
    for fmt in ("%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            pass
    raise ValueError(f"no valid date format found: {date_string}")


def calculate_pips(pair: str, price: float) -> float:
    '''Function to calculate the number of pips
    for a given price

    Args:
        pair : Currency pair used in the trade. i.e. AUD_USD
        price : Provided price

    Returns:
        Number of pips
    '''
    pips = None
    (first, second) = pair.split("_")
    if first == 'JPY' or second == 'JPY':
        pips = price * 100
    else:
        pips = price * 10000

    return '%.1f' % pips


def add_pips2price(pair: str, price: float, pips: int) -> float:
    '''Function that gets a price value and adds
    a certain number of pips to the price.

    Arguments:
        pair : Currency pair used in the trade. i.e. AUD_USD
        price : Price
        pips : Number of pips to increase

    Returns:
        New price
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


def substract_pips2price(pair: str, price: float, pips: int) -> float:
    '''Function that gets a price value and substracts
    a certain number of pips to the price

    Arguments:
        pair : Currency pair used in the trade. i.e. AUD_USD
        price : Price to modify
        pips : Number of pips to decrease

    Returns:
        New price
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


def periodToDelta(ncandles: int, timeframe: str):
    """Function that receives an int representing a number of candles using
    the 'ncandles' param and returns a datetime timedelta object

    Arguments:
        ncandles: Number of candles for which the timedelta will be retrieved
        timeframe: Timeframe used for getting the delta object. Possible
                   values are:
                   2D,D,H12,H10,H8,H4

    Returns:
        datetime timedelta object
    """
    patt = re.compile(r"(\d)D")

    delta = None
    if patt.match(timeframe):
        raise Exception(f"{timeframe} is not valid. Oanda rest service does not take it")
    elif timeframe == 'D':
        delta = timedelta(hours=24 * ncandles)
    else:
        fgran = timeframe.replace('H', '')
        delta = timedelta(hours=int(fgran) * ncandles)

    return delta


def get_ixfromdatetimes_list(datetimes_list, d) -> int:
    """Function to get the index of the element that is closest
    to the passed datetime

    Arguments:
        datetimes_list : list
                     List with datetimes
        d : datetime

    Returns:
        index of the closest datetime to d
    """

    sel_ix = None
    diff = None
    ix = 0
    for ad in datetimes_list:
        if diff is None:
            diff = abs(ad-d)
            sel_ix = ix
        else:
            if abs(ad-d) < diff:
                sel_ix = ix
                diff = abs(ad-d)
        ix += 1

    return sel_ix


def pairwise(iterable):
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return zip(a, a)


def correct_timeframe(settings, timeframe):
    """This utility function is used for correcting
    all the pips-related settings depending
    on the selected timeframe

    Arguments:
        settings: ConfigParser object
        timeframe : D,H12,H8,4

    Returns:
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


def calculate_profit(prices: Tuple[float, float],
                     type: str, pair: str) -> float:
    """Function to calculate the profit (in pips)
    defined as the difference between 2 prices.

    Args:
        prices: tuple with the 2 prices to compare [price, entry]
        type: ['long'/'short']
        pair: instrument
    """
    if (prices[0] - prices[1]) < 0:
        sign = -1 if type == "long" else 1
    else:
        sign = 1 if type == "long" else -1
    pips = float(calculate_pips(pair,
                                abs(prices[0]-prices[1]))) * sign
    return pips


def is_even_hour(d: datetime) -> bool:
    """Check if hour in datetime is even"""
    if d.hour % 2 == 0:
        return True
    elif d.hour % 2 != 0:
        return False


def is_week_day(d: datetime) -> bool:
    """Returns True if 'd' falls on a weekday"""

    is_weekday = d.isoweekday() < 6
    return is_weekday


def load_config_yaml_file(yaml_file: str) -> dict:
    """Loads a yaml file into a dict"""
    with open(yaml_file, 'r') as file:
        config = yaml.safe_load(file)
        return config
