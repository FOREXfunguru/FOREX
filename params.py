from dataclasses import dataclass
from utils import DATA_DIR

@dataclass
class gparams:
    """General paramaters"""
    # Folder to store all output files
    outdir : str = f"{DATA_DIR}/out/"
    # Increase verbosity
    debug : bool = True
    # candle's body percentage below which the candle will be considered
    # indecision candle
    ic_perc : int = 20
    # size of images
    size = (20, 10)

@dataclass
class tjournal_params:
    # Column names that will be written in the output worksheet
    colnames : str = 'id,timeframe,start,end,strat,type,entry,session,TP,SL,SR,tot_SR,rank_selSR,entry_time,outcome,pips,SLdiff,lasttime,pivots,pivots_lasttime,total_score,score_lasttime,score_pivot,score_pivot_lasttime,trend_i,entry_onrsi,pips_c_trend,max_min_rsi'

@dataclass
class counter_params:
    # number of candles from start to calculate max,min RSI
    rsi_period : int = 20

@dataclass
class tradebot_params:
    # quantile used as threshold for selecting S/R
    th : float = 0.70
    # invoke 'calc_SR' each 'period' number of candles
    period : int = 60
    # number of candles to go back for calculating S/R price
    # range. This is relevant for trade_bot's get_max_min function and it will
    # also be relevant to decide how much to go back in time to detect SRs
    period_range : int = 1500
    # add this number of pips to SL and entry
    add_pips : int = 10
    # Risk Ratio for trades
    RR : float = 1.5
    # adjust_SL type
    adj_SL : str = 'candles'
    # adjust_SL_pips number of pips
    adj_SL_pips : int = 100
    # do not consider trades with an ic with height>than 'max_height' pips
    max_height : int = 150

    def __post_init__(self):
        if not self.adj_SL in ['candles', 'pips', 'nextSR']:
            raise ValueError(f"{self.adj_SL} is not a valid for adj_SL")

@dataclass
class pivots_params:
    # Number of pips above/below SR to identify bounces                                                                                                          \
    hr_pips : int = 25
    # Value used by ZigZag to identify pivots. The lower the
    # value the higher the sensitivity
    th_bounces : float = 0.02
    # (int) Skip merge if Segment is greater than 'n_candles'
    n_candles : int = 18
    # (int) % of diff in pips threshold
    diff_th : int = 50
    # Boolean, if true then produce png files for in_area pivots and rsi_bounces
    plot : bool = True
    # Bool. run merge_pre's function from Pivot class
    runmerge_pre : bool = True
    # Bool. run merge_aft's function from Pivot class
    runmerge_aft : bool = True

@dataclass
class clist_params:
    #  Number of candles used for calculating the RSI
    rsi_period : int = 14
    # SR detection
    i_pips : int = 30
    # Minimum number of candles from start to be required
    min : int = 5

@dataclass
class trade_params:
    # When using run method, how many pips above/below the HArea will considered
    # to check if it hits the entry,SL or TP
    hr_pips : int = 1
    # number of candles from start of trade to run the trade and assess the outcome
    numperiods : int = 300
    # granularity for HArea.get_cross_time
    granularity : str = 'H2'
    # num of candles from trade.start to calc ATR
    period_atr : int = 20
    # number of candles to go back when init_clist=True
    trade_period: int = 5000
    # number of pips to add/substract to SR to calculate lasttime
    pad: int = 30
    ## trade management 
    strat: str = "standard" # if 'exit_early' then close the trade if price is in profit and 
                              # trade as been active for more than trade_params.no_candles.
                              # if 'standard' then wait to check if trade finishes up to trade_params.numperiods
    no_candles: int = 150
    reduce_perc: int = 50 # reduce the diff between TP and entry to this 'reduce_perc' %