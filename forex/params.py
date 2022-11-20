from dataclasses import dataclass, field
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
    ic_perc : int = 15
    # size of images
    size = (20, 10)

@dataclass
class tjournal_params:
    # Column names that will be written in the output worksheet
    colnames : str = 'id,timeframe,start,strat,type,entry,session,TP,SL,SR,tot_SR,rank_selSR,entry_time,outcome,pips,SLdiff,lasttime,pivots,\
                     pivots_lasttime,total_score,score_lasttime,score_pivot,score_pivot_lasttime,trend_i,entry_onrsi,\
                     pips_c_trend,max_min_rsi'

@dataclass
class counter_params:
    # number of candles from start to calculate max,min RSI
    rsi_period : int = 20
    # Comma-separated list of strategies used for applying the Counter pattern
    strats : str = 'counter'
    # number of candles that the counter trade will have
    period : int = 4000
    # Bool. run merge_pre's function from Pivot class
    runmerge_pre : bool = True
    # Bool. run merge_aft's function from Pivot class
    runmerge_aft : bool = True
    # Generate *.png files
    doPlot : bool = True

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
    # last pivot should be considered
    last_pivot : bool = False
    # Bool. run merge_pre's function from Pivot class
    runmerge_pre : bool = True
    # Bool. run merge_aft's function from Pivot class
    runmerge_aft : bool = True

@dataclass
class harea_params:
    # Minimum number of candles from start to be required
    min : int = 5
    # Width of S/R area also to identify last_time
    hr_pips : int = 100

@dataclass
class clist_params:
    # This is relevant for 'calc_rsi'. Number of candles before this CandleList start
    # for which close price data will be fetched. The larger the number of candles
    # the more accurate the ewm calculation will be, as the exponential moving average
    # calculated for each of the windows (of size=rsi_period) will be directly affected
    # by the previous windows in the series
    period : int = 4000
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
    granularity : str = 'H8'
    # num of candles from trade.start to calc ATR
    period_atr : int = 20

@dataclass
class tradebot_params:
    # quantile used as threshold for selecting S/R
    th : float = 0.70
    # invoke 'calc_SR' each 'period' number of candles
    period : int = 30
    # number of candles to go back for calculating S/R price
    # range. This is relevant for trade_bot's get_max_min function and it will
    # also be relevant to decide how much to go back in time to detect SRs
    period_range : int = 1500
    # add this number of pips to max,min for price range to detect S/Rs
    add_pips : int = 200
    # Risk Ratio for trades
    RR : float = 1.5
    # if true, then a pickled representation of a
    # list of tuples (datetime, HAreaList)
    # will be generated. Default: False
    store_SRlist : bool = True
    # if true, then a pickled representation of a
    # list of tuples (datetime, HAreaList)
    # will be used and calc_SR will be skipped.
    # Default: False
    load_SRlist : bool = False
    # if True, then the trade.run method will be invoked
    run_trades : bool = False

@dataclass
class itrend_params:
    # Value used by ZigZag to identify pivots for getting the start
    # of the trend. The lower the
    # value the higher the sensitivity.
    th_bounces : float = 0.02
    # These are the merge_pre parameters
    n_candles : int = 12
    diff_th : int = 50

