from __future__ import division
from apis.oanda_api import Reversal
from apis.oanda_api import BiCandle
import pandas as pd
import logging
import warnings

logging.basicConfig(level=logging.INFO)
logging.info("Program started")


xls_file = pd.ExcelFile('/Users/ernesto/Google_Drive/MONEDAS/backtesting/data_collection_29012017stripped.xlsx')
'''
xls_file = pd.ExcelFile('/Users/ernesto/Google_Drive/MONEDAS/backtesting/test.xlsx')
'''
df = xls_file.parse('Sheet1')

newline=""
out=open('/Users/ernesto/projects/FOREX/out.txt','w')
out.write("instrument\tgranularity\tdate time\ttype\toutcome\tengulfing?\tICdiffm1_wh\tICdiffm1_wl\tp1diffIC_wh\tp1diffIC_wl\tICdiffm1_ch\tICdiffm1_cl\tp1diffIC_ch\tp1diffIC_cl\t[perc_uwick:perc_body:perc_lwick]p1\tcolors_pre_[m1,ic]\tcolors_post_[ic,p1]\tformation_pre_[m1,ic]\tformation_post_[ic,p1]\tavg_volume_pre\tvolume_pre_[m1,ic]\tvolume_post_[ic,p1]\n")

for index, row in df.iterrows():
    warnings.warn("INFO: Analysing %s:%s" % (row['pair'],row['date']))
    candlelist_post=[]
    candlelist_pre=[]
    if row['outcome']==1: outcome=True
    if row['outcome']==0: outcome=False
    newline="%s\t%s\t%s\t%s\t%s" % (row['pair'], row['granularity'], row['date'], row['type'], str(outcome))
    ic=row['date']
    r=Reversal(ic=str(row['date']),outcome=True,number_pre=3,number_post=3,instrument=row['pair'],granularity=row['granularity'],type=row['type'])
    candlelist_post.append(r.ic_candle)
    candlelist_post.append(r.post_candles[0])
    candlelist_pre.append(r.pre_candles[-1])
    candlelist_pre.append(r.ic_candle)
    bc=BiCandle(candleA=candlelist_post[0],candleB=candlelist_post[1])
    newline= newline+"\t"+ str(bc.is_engulfing()) +"\t"
    
    listpost_upper_wick=r.get_differential(candlelist_post,'upper',entity='wick')
    listpost_lower_wick=r.get_differential(candlelist_post,'lower',entity='wick')
    listpre_upper_wick=r.get_differential(candlelist_pre,'upper',entity='wick')
    listpre_lower_wick=r.get_differential(candlelist_pre,'lower',entity='wick')
    for i, j in zip(listpre_upper_wick, listpre_lower_wick):
        newline= newline+"%f\t%f\t" % (i,j)
    for i, j in zip(listpost_upper_wick, listpost_lower_wick):
        newline= newline+"%f\t%f\t" % (i,j)
        
    listpost_upper_candle=r.get_differential(candlelist_post,'upper',entity='candle')
    listpost_lower_candle=r.get_differential(candlelist_post,'lower',entity='candle')
    listpre_upper_candle=r.get_differential(candlelist_pre,'upper',entity='candle')
    listpre_lower_candle=r.get_differential(candlelist_pre,'lower',entity='candle')
    for i, j in zip(listpre_upper_candle, listpre_lower_candle):
        newline= newline+"%f\t%f\t" % (i,j)
    for i, j in zip(listpost_upper_candle, listpost_lower_candle):
        newline= newline+"%f\t%f" % (i,j)
    
    newline=newline+"\t[%f:%f:%f]" %(candlelist_post[1].perc_uwick,candlelist_post[1].perc_body,candlelist_post[1].perc_lwick)
    
    colors_pre="{0}"
    colors_pre=",".join(colors_pre.format(c.colour) for c in candlelist_pre)
    colors_post="{0}"
    colors_post=",".join(colors_post.format(c.colour) for c in candlelist_post)
    
    newline=newline+"\t"+colors_pre+"\t"+colors_post
    
    formation_pre="{0}"
    formation_pre=",".join(formation_pre.format(c.representation) for c in candlelist_pre)
    formation_post="{0}"
    formation_post=",".join(formation_post.format(c.representation) for c in candlelist_post)
    newline=newline+"\t"+formation_pre+"\t"+formation_post+"\t"
    
    sum_pre_candles=sum(c.volume for c in r.pre_candles)
    avg_vol_pre=sum_pre_candles/len(r.pre_candles)
    
    volume_pre="{0}"
    volume_pre=",".join(volume_pre.format(c.volume) for c in candlelist_pre)
    volume_post="{0}"
    volume_post=",".join(volume_post.format(c.volume) for c in candlelist_post)
    
    newline=newline+ '%.2f' % avg_vol_pre+"\t"+volume_pre+"\t"+volume_post+"\n"
    
    out.write(newline)
    
out.close()
logging.info("Done!")
