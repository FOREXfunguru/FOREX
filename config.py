import datetime


PROJECT = {
    'root' :'/Users/ernesto/projects/FOREX/CT/'
}

OANDA_API = {
    'url': 'https://api-fxtrade.oanda.com/v1/candles?',
    'alignmentTimezone' : 'Europe/London',
    'dailyAlignment': 22

}

#configuration for Counter doubletop pattern
CTDBT = {
    'period' : 4000, # number of candles from self.start that will be considered in order to
                     # to look for peaks/valleys
    'HR_pips' : 50, # number of pips over/below S/R used for trying to identify bounces
    'HR_pips_2nd' : 100, # number of pips over/below S/R used for trying to identify the 2nd bounce
    'step_pips': 5, # number of pips to increase HR_pips in order to widen the area to look for bounces
    'max_HRpips' : 500, # max number of pips that will be used in order to widen the area to look for bounces
    'min_dist' : 10, # Minimum distance between peaks
    'period1st_bounce' : 5, # Controls the maximum number of candles allowed between
                           # self.start and this 'period1st_bounce' in order look for the 1st bounce
    'period2nd_bounce': 75,  # Controls the maximum number of candles allowed between
                             # datetime controlled by 'period1st_bounce' and datetime controlled by 'period2nd_bounce'
                             # in order to detect the 2nd bounce
    'period_trend': 500, # Controls the maximum number of candles before self.bounce_2nd in order to look for start
                         # of trend
    'period_divergence' : 30, # Number of candles to consider before 2nd_bounces in order to look for peaks/valleys in
                             # rsi
    'number_of_rsi_bounces' : 3, # Number of rsi bounces from last (most recent) to consider for calculating divergence
    'threshold_1st_2nd_bounces' : 0.00, # Threshold pivot detection for 1st and 2nd bounces
    'threshold_rest_bounces' : 0.01, # Threshold pivot detection for bounces after the 2nd bounce
    'part' : 'openAsk' # What part of the candles to use in the different calculations
}

#configuration for Counter pattern
CT = {
    'HR_pips': 75,  # number of pips over/below S/R used for trying to identify bounces
    'period': 4000, # number of candles from self.start that will be considered in order to
                     # to look for peaks/valleys
    'threshold_bounces': 0.04, # Threshold pivot detection for bounces
    'part': 'closeAsk',  # What part of the candles to use in the different calculations
    'png_prefix':  PROJECT['root'] + "/bounce_images/counter"
}


# start datetime for Oanda's historical data
START_HIST = {
        'AUD_CAD': datetime.datetime(2004, 6, 5, 21, 0),
        'AUD_JPY': datetime.datetime(2004, 6, 5, 21, 0),
        'AUD_NZD': datetime.datetime(2004, 5, 30, 21, 0),
        'AUD_USD': datetime.datetime(2002, 6, 5, 21, 0),
        'CAD_JPY': datetime.datetime(2004, 6, 5, 21, 0),
        'EUR_AUD': datetime.datetime(2004, 6, 5, 21, 0),
        'EUR_CAD': datetime.datetime(2004, 6, 5, 21, 0),
        'EUR_CHF': datetime.datetime(2002, 6, 5, 21, 0),
        'EUR_GBP': datetime.datetime(2002, 5, 7, 21, 0),
        'EUR_JPY': datetime.datetime(2002, 6, 5, 21, 0),
        'EUR_USD': datetime.datetime(2002, 6, 5, 21, 0),
        'EUR_NZD': datetime.datetime(2002, 6, 5, 21, 0),
        'GBP_AUD': datetime.datetime(2004, 6, 5, 21, 0),
        'GBP_JPY': datetime.datetime(2002, 6, 5, 21, 0),
        'GBP_USD': datetime.datetime(2002, 6, 5, 21, 0),
        'NZD_CAD': datetime.datetime(2004, 6, 1, 21, 0),
        'NZD_JPY': datetime.datetime(2004, 6, 1, 21, 0),
        'NZD_USD': datetime.datetime(2002, 9, 5, 21, 0),
        'USD_CAD': datetime.datetime(2002, 5, 19, 21, 0),
        'USD_CHF': datetime.datetime(2002, 6, 5, 21, 0),
        'USD_JPY': datetime.datetime(2002, 5, 1, 21, 0),
        'AUD_CHF': datetime.datetime(2004, 6, 5, 21, 0),
        'USD_NOK': datetime.datetime(2004, 6, 5, 21, 0),
        'USD_SEK': datetime.datetime(2004, 6, 5, 21, 0),
        'CAD_CHF': datetime.datetime(2004, 6, 5, 21, 0),
        'CHF_JPY': datetime.datetime(2004, 6, 5, 21, 0),
}

PNGFILES = {
    'fig_sizes' : (20, 10), # tuple controlling the size of figures
    'regression' : PROJECT['root']+'regresion_imgs/',
    'bounces' : PROJECT['root']+'bounce_images/',
    'rsi': PROJECT['root'] + 'rsi_images/',
    'init_trend' : PROJECT['root']+'init_trend_imgs/',
    'div' : PROJECT['root']+'divergence_plots/'
}

TREND = {
    'diff_th' : 200 # Number of pips used as threshold in the retrace number of pips
                    # in the detection of trend
}

SRarea = {
    'period' : 1000, # Number of candles used for identifying the SR areas
    'th_up' : 0.01,
    'th_down' : -0.01
}

SEGMENT = {
    'min_n_candles' : 10, # Minimum number of candles in order not be considered a short segment
    'diff_in_pips' : 200 # Below this number of pips the segment will be short
}

#List with valid strategies from the trade_journal trades
VALID_STRATS = ['counter','counter_sma','counter_beftrade','cont','counter_dbtp','counter_aftrade', 'counter_b1',
                'counter_b2','counter_b3', 'counter_b4']