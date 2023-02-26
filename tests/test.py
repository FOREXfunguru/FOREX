from forex.candle import CandleList
from api.oanda.connect import Connect

import pdb
import sys
conn = Connect(
        instrument="AUD_USD",
        granularity='D')

clO = conn.query('2010-11-16T22:00:00', '2020-11-19T22:00:00')
clO.pickle_dump('clist_audusd_2010_2020.pckl')
print("h")