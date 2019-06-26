

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