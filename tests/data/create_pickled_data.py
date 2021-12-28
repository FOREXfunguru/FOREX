from forex.segment import SegmentList, Segment
from forex.candle import CandleList
from utils import DATA_DIR
from forex.pivot import PivotList

# pickle Segment
clObj = CandleList.pickle_load(DATA_DIR+"/clist_audusd_2010_2020.pckl")
pl = PivotList(clist=clObj)
pl.slist[5].pickle_dump('seg_audusd.pckl')
pl.slist[6].pickle_dump('seg_audusdB.pckl')

#pickle SegmentList
pl.slist.pickle_dump('seglist_audusd.pckl')

