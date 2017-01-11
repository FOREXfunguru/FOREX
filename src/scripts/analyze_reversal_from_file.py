from OandaAPI import OandaAPI,Reversal
import pandas as pd
from pandas.tseries.offsets import BDay
import logging

logging.basicConfig(level=logging.INFO)
logging.info("Program started")

oanda=OandaAPI()

list=oanda.fetch_candles_from_file("/Users/ernesto/projects/FOREX/data/21_04_15.txt")

ic="2015-04-20"

r=Reversal(list,True)

p_highBid=0.0
p_lowBid=0.0
middle=(len(list)/2)
for k,i in enumerate(list):
    if(k==0):
        p_highBid=float(i.highBid)
        p_lowBid=float(i.lowBid)
    else:
        c_highBid=float(i.highBid)-p_highBid
        c_lowBid=float(i.lowBid)-p_lowBid
        print "highBid:%s lowBid:%s time:%s" % (c_highBid,c_lowBid,i.time)
        p_highBid=float(i.highBid)
        p_lowBid=float(i.lowBid)
        print "h"

logging.info("Done!")
