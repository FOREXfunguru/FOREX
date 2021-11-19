from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Params:
    alignmentTimezone : int = 22
    dailyAlignment : str = 'Europe/London'
    url : str = 'https://api-fxtrade.oanda.com/v3/instruments/'
    roll : bool = True # If True, then extend the end date, which falls on close market, to the next period for which
                       # the market is open. Default=False
    content_type : str = 'application/json'
    pairs_start : Dict[str,str] = field(default_factory=lambda: {
                                                                 'AUD_CAD' : '2004-06-05T21:00:00',
                                                                 'AUD_JPY' : '2004-05-31T21:00:00',
                                                                 'AUD_NZD' : '2004-05-01T21:00:00',
                                                                 'AUD_USD' : '2002-06-05T21:00:00',
                                                                 'CAD_JPY' : '2004-06-05T21:00:00',
                                                                 'EUR_AUD' : '2004-06-05T21:00:00',
                                                                 'EUR_CAD' : '2004-05-31T21:00:00',
                                                                 'EUR_CHF' : '2002-06-02T21:00:00',
                                                                 'EUR_CZK' : '2002-05-06T21:00:00',
                                                                 'EUR_GBP' : '2002-05-07T21:00:00',
                                                                 'EUR_JPY' : '2002-05-06T21:00:00',
                                                                 'EUR_USD' : '2002-06-05T21:00:00',
                                                                 'EUR_NZD' : '2004-05-31T21:00:00',
                                                                 'GBP_AUD' : '2004-06-05T21:00:00',
                                                                 'GBP_CAD' : '2004-05-31T21:00:00',
                                                                 'GBP_JPY' : '2002-05-07T21:00:00',
                                                                 'GBP_USD' : '2002-05-06T21:00:00',
                                                                 'GBP_NZD' : '2004-05-31T21:00:00',
                                                                 'NZD_CAD' : '2004-05-31T21:00:00',
                                                                 'NZD_CHF' : '2004-05-31T21:00:00',
                                                                 'NZD_JPY' : '2004-05-31T21:00:00',
                                                                 'NZD_USD' : '2002-09-23T21:00:00',
                                                                 'USD_CAD' : '2002-05-07T21:00:00',
                                                                 'USD_CHF' : '2002-05-06T21:00:00',
                                                                 'USD_JPY' : '2002-05-06T21:00:00',
                                                                 'AUD_CHF' : '2004-05-31T21:00:00',
                                                                 'USD_NOK' : '2003-09-01T21:00:00',
                                                                 'USD_SEK' : '2004-05-31T21:00:00',
                                                                 'CAD_CHF' : '2004-05-31T21:00:00',
                                                                 'CHF_JPY' : '2004-05-31T21:00:00',
                                                                 'GBP_CHF' : '2002-05-07T21:00:00'})