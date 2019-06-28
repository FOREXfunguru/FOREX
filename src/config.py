import datetime


PROJECT = {
    'root' :'/Users/ernesto/PycharmProjects/FOREX/scripts/'
}

OANDA_API = {
    'url': 'https://api-fxtrade.oanda.com/v1/candles?',
    'alignmentTimezone' : 'Europe/London',
    'dailyAlignment': 22

}

#configuration for Counter doubletop
CTDBT = {
    'period' : 4500, # number of candles from self.start to self.start-period that will be considered in order to
                    # to look for the double peak/valley,
    'HR_pips' : 30, #  number of pips over/below S/R used for trying to identify bounces
    'threshold' : 0.5, # threshold for detecting peaks.
    'min_dist' : 5, # Minimum distance between peaks
    'period1st_bounce' : 8 # Controls the maximum number of candles allowed between
                           # self.start and the location of the most recent bounce

}

# start datetime for Oanda's historical data
START_HIST = {
    'AUD_CAD': datetime.datetime(2004, 6, 5, 21, 0),
    'AUD_JPY': datetime.datetime(2004, 6, 5, 21, 0),
    'AUD_NZD': datetime.datetime(2004, 6, 5, 21, 0),
    'AUD_USD': datetime.datetime(2002, 6, 5, 21, 0),
    'CAD_JPY': datetime.datetime(2004, 6, 5, 21, 0),
    'EUR_AUD': datetime.datetime(2004, 6, 5, 21, 0),
    'EUR_CAD': datetime.datetime(2004, 6, 5, 21, 0),
    'EUR_CHF': datetime.datetime(2002, 6, 5, 21, 0),
    'EUR_GBP': datetime.datetime(2002, 6, 5, 21, 0),
    'EUR_JPY': datetime.datetime(2002, 6, 5, 21, 0),
    'EUR_USD': datetime.datetime(2002, 6, 5, 21, 0),
    'GBP_AUD': datetime.datetime(2004, 6, 5, 21, 0),
    'GBP_JPY': datetime.datetime(2002, 6, 5, 21, 0),
    'GBP_USD': datetime.datetime(2002, 6, 5, 21, 0),
    'NZD_CAD': datetime.datetime(2004, 6, 1, 21, 0),
    'NZD_JPY': datetime.datetime(2004, 6, 1, 21, 0),
    'NZD_USD': datetime.datetime(2002, 9, 5, 21, 0),
    'USD_CAD': datetime.datetime(2002, 6, 5, 21, 0),
    'USD_CHF': datetime.datetime(2002, 6, 5, 21, 0),
    'USD_JPY': datetime.datetime(2002, 6, 5, 21, 0),
    'AUD_CHF': datetime.datetime(2004, 6, 5, 21, 0),
}

PNGFILES = {
    'regression' : PROJECT['root']+'regresion_imgs/',
    'bounces' : PROJECT['root']+'bounce_images/'
}
