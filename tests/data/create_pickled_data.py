from forex.segment import SegmentList, Segment
from forex.candle import CandleList
from utils import DATA_DIR
from forex.pivot import PivotList
from api.oanda.connect import Connect

# pickle CandleList Daily
conn = Connect(
        instrument="AUD_USD",
        granularity='D')
clO = conn.query('2010-11-16T22:00:00', '2020-11-19T22:00:00')
clO.pickle_dump(f"{DATA_DIR}/clist_audusd_2010_2020.pckl")

# pickle CandleLists H8
conn = Connect(
        instrument="AUD_USD",
        granularity='H8')
clO = conn.query("2021-01-03T22:00:00", "2021-12-31T14:00:00")
clO.pickle_dump(f"{DATA_DIR}/clist.AUDUSD.H8.2021.pckl")

clO = conn.query("2019-01-03T22:00:00", "2019-12-31T14:00:00")
clO.pickle_dump(f"{DATA_DIR}/clist.AUDUSD.H8.2019.pckl")


# pickle Segment
clObj = CandleList.pickle_load(f"{DATA_DIR}/clist_audusd_2010_2020.pckl")
pl = PivotList(clist=clObj)
pl.slist[5].pickle_dump('seg_audusd.pckl')
pl.slist[6].pickle_dump('seg_audusdB.pckl')

#pickle SegmentList
pl.slist.pickle_dump('seglist_audusd.pckl')

