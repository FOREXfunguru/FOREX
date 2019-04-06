import pdb

from Pattern.Counter import Counter


class CounterDbTp(Counter):
    '''
    This class represents a trade showing Counter doubletop pattern (inherits from Counter)

    Class variables
    ---------------

    start: datetime, Required
           Time/date when the trade was taken. i.e. 20-03-2017 08:20:00s
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    trend_i: datetime, Required
             start of the trend
    type: str, Optional
          What is the type of the trade (long,short)
    SL:  float, Optional
         Stop/Loss price
    TP:  float, Optional
         Take profit price
    SR:  float, Optional
         Support/Resistance area
    bounce_1st : with tuple (datetime,price) containing the datetime
                 and price for this bounce
    bounce_2nd : with tuple (datetime,price) containing the datetime
                 and price for this bounce
    rsi_1st : bool, Optional
              Is price in overbought/oversold
              area in first peak
    rsi_2nd : bool, Optional
              Is price in overbought/oversold
              area in second peak
    '''

    def __init__(self, pair, start, **kwargs):

        self.start = start

        allowed_keys = ['timeframe', 'period', 'trend_i', 'type', 'SL',
                        'TP', 'SR']
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)
        super().__init__(pair)

    def set_2ndbounce(self):
        '''
        Function to set bounce_2nd (the one that is the most recent)
        and rsi_2nd class attributes

        Returns
        -------
        Nothing
        '''

        self.set_bounces(part='openAsk')
        self.bounce_2nd=self.bounces[-1]

        pdb.set_trace()

        # now check rsi for this bounce
        candle = self.clist_period.fetch_by_time(self.bounce_2nd[0])

        isonrsi = False

        if candle.rsi >= 70 or candle.rsi <= 30:
            isonrsi = True

        self.rsi_2nd = isonrsi