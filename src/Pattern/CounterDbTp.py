

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
    type: str, Optional
          What is the type of the trade (long,short)
    SL:  float, Optional
         Stop/Loss price
    TP:  float, Optional
         Take profit price
    SR:  float, Optional
         Support/Resistance area
    bounce_1st : datetime. Optional
                 Datetime for first bounce
    bounce_2nd : datetime. Optional
                 Datetime for second bounce
    rsi_1st : bool, Optional
              Is price in overbought/oversold
              area in first peak
    rsi_2nd : bool, Optional
              Is price in overbought/oversold
              area in second peak
    '''

    def __init__(self,
                 start,
                 pair,
                 timeframe,
                 type=None,
                 SL=None,
                 TP=None,
                 SR=None,
                 bounce_1st=None,
                 bounce_2nd=None,
                 rsi_1st=None,
                 rsi_2nd=None):
        super().__init__(start,pair,timeframe,type,SL,TP,SR)
        self.bounce_1st = bounce_1st
        self.bounce_2nd = bounce_2nd
        self.rsi_1st = rsi_1st
        self.rsi_2nd = rsi_2nd
