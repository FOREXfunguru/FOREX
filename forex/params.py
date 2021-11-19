from dataclasses import dataclass, field

@dataclass
class Params:
    period : int = 4000
    rsi_period : int = 14
    min : int = 5 # Minimum number of candles from start to be required
    outdir : str = '../data/imgs'
    # Value used by ZigZag to identify pivots for getting the start
    # of the trend. The lower the
    # value the higher the sensitivity.
    th_bounces : float = 0.02
    n_candles : int = 12
    diff_th : float = 50

