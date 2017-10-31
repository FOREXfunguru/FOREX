from __future__ import division
import pandas as pd
import re

def get_number_of_0s(sequence,norm=True):
    a_list=list(sequence)
    new_list=[a_number for a_number in a_list if a_number=='0']
    if norm is True:
        return len(new_list)/len(a_list)
    else:
        return len(new_list)

def get_number_of_double0s(seq1,seq2,norm=True):
    list1=list(seq1)
    list2=list(seq2)

    if len(list1) != len(list2):
        raise Exception("Lengths of seq1 and seq2 are not equal")

    number_of_double0s=0
    for i, j in zip(list1, list2):
        if int(i)==0 and int(j)==0:
            number_of_double0s=number_of_double0s+1

    if norm is True:
        return number_of_double0s/len(list1)
    else:
        number_of_double0s

def get_longest_stretch(seq):
    length=len(max(re.compile("(0+0)*").findall(seq)))

    return length
        
    
xls_file = pd.ExcelFile('/Users/ernesto/lib/FOREX/src/scripts/Trading_journal_07082017.xlsx')
writer = pd.ExcelWriter('trend_momentum.xlsx')

df = xls_file.parse('trend_momentum_analysis',converters={'High Sequence': str,
                                                          'Open': str,
                                                          'Low Sequence' : str,
                                                          'Close': str,
                                                          'Color Sequence': str})

high_0s=[]
open_0s=[]
low_0s=[]
close_0s=[]
color_0s=[]
highlows_double0s=[]
openclose_double0s=[]
stretch_high=[]
stretch_open=[]
stretch_close=[]
stretch_low=[]
stretch_color=[]

for index, row in df.iterrows():
    print(row['Start of trade'])
    number_high0s='%.2f' % get_number_of_0s(row['High Sequence'],norm=True)
    number_open0s='%.2f' % get_number_of_0s(row['Open'],norm=True)
    number_low0s='%.2f' % get_number_of_0s(row['Low Sequence'],norm=True)
    number_close0s='%.2f' % get_number_of_0s(row['Close'],norm=True)
    number_color0s='%.2f' % get_number_of_0s(row['Color Sequence'],norm=True)
    high_0s.append(number_high0s)
    open_0s.append(number_open0s)
    low_0s.append(number_low0s)
    close_0s.append(number_close0s)
    color_0s.append(number_color0s)

    # double 0s
    number_highlow_double0s='%.2f' % get_number_of_double0s(row['High Sequence'],row['Low Sequence'],norm=True)
    number_openclose_double0s='%.2f' % get_number_of_double0s(row['Open'],row['Close'],norm=True)
    highlows_double0s.append(number_highlow_double0s)
    openclose_double0s.append(number_openclose_double0s)

    # longest stretch
    longest_high=get_longest_stretch(row['High Sequence'])
    longest_open=get_longest_stretch(row['Open'])
    longest_low=get_longest_stretch(row['Low Sequence'])
    longest_close=get_longest_stretch(row['Close'])
    longest_color=get_longest_stretch(row['Color Sequence'])
    stretch_high.append(longest_high)
    stretch_open.append(longest_open)
    stretch_close.append(longest_close)
    stretch_low.append(longest_low)
    stretch_color.append(longest_color)

df['high_0s']=high_0s
df['open_0s']=open_0s
df['low_0s']=low_0s
df['close_0s']=close_0s
df['color_0s']=color_0s
df['highlows_double0s']=highlows_double0s
df['openclose_double0s']=openclose_double0s
df['stretch_high']=stretch_high
df['stretch_open']=stretch_open
df['stretch_close']=stretch_close
df['stretch_low']=stretch_low
df['stretch_color']=stretch_color

df.to_excel(writer,'trend_momentum')
writer.save()

print("h")
