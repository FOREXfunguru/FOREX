
# coding: utf-8

import pandas as pd
import numpy as np
import pdb
import re
import argparse
import os
import json
import numbers

from sklearn.preprocessing import Imputer

parser = argparse.ArgumentParser(description='Script to calculate the score for counter doubletop trades')

parser.add_argument('--ifile', required=True, help='input file containing the training trades. Valid formats are .csv or .tsv')
parser.add_argument('--timeframe', required=True, help='Input dataframe. Valid values are: ALL,D,H12,H6')
parser.add_argument('--attrbs', required=True, help='Json file calculated by train_for_continuations.py')
parser.add_argument('--prefix', required=True, help='Prefix for .csv file with scores in it')
parser.add_argument('--verbose', required=False, default=False, help='Increase verbosity')
args = parser.parse_args()

ext=os.path.splitext(args.ifile)[1]

separator=None
if ext == '.tsv':
    separator="\t"
elif ext == '.csv':
    separator=","
else:
    raise Exception("Extension {0} is not recognized".format(ext))

def str_to_bool(s):
    if s == 'True':
         return True
    elif s == 'False' or s == False:
         return False
    else:
         raise ValueError # evil ValueError that doesn't tell you what the wrong value was

with open(args.attrbs, "r") as read_file:
    data = json.load(read_file)
         
#read-in the data
DF=pd.read_csv(args.ifile,sep=separator,na_values=["n.a.","n.a"])

print("Total # of records: {0}; # of variables: {1}".format(DF.shape[0], DF.shape[1]))

if not args.timeframe in ['ALL','D','H12','H8','H4']:
    raise Exception("{0} timeframe is not valid".format(args.timeframe))

if args.timeframe != 'ALL':
    DF=DF[DF['timeframe']==args.timeframe]

print("Total # of records for desired timeframe: {0}; # of variables: {1}".format(DF.shape[0], DF.shape[1]))

# Calculate win-rate
print("Win rate 1st peak")
print(DF['outcome 1st peak'].value_counts(normalize=True))

print("Win rate 2nd peak")
print(DF['outcome 2nd peak'].value_counts(normalize=True))


#
# Convert to datetime the relevant variables
#

for v in ['start 1st peak','last time 1st peak']:
    DF[v]= pd.to_datetime(DF[v])


#
# last time 
# This datetime variable represents the last time the price was over/below the entry price level.
# The first to do is to create a new datetime variable representing the difference (in days) between
# the entry datetime (start column) and the last time datetime

DF['diff']=(DF['start 1st peak']-DF['last time 1st peak'])
DF['diff']=DF['diff'].apply(lambda x: x.days)


# ### Pips_ratio
# This variable contains the ratio between 'length in pips'/'length of trend (-1)'
DF['pips_ratio']=DF['length in pips'].astype(int)/DF['length of trend 1st peak'].astype(int)

transl_dict={ 
        'S':1,
        'F':0, 
        True:1, 
        False:0
    }
def digit_binary(x,transl_dict,name):
    '''
    This function will replace the values in categorical
    binary variables by 1 and 0
    
    Parameters
    ----------
    transl_dict: dict
                 Keys will be the old categorical names and Values
                 will be 1 and 0. For example:
                 transl_dict={ 
                            'S':1,
                            'F':0, 
                            True:1, 
                            False:0
                            }
    name: str
          Name of the column to modify
        
    Returns
    -------
    The new label for the categorical variable
    '''
    
    return transl_dict[x[name]]

DF['outcome 1st peak']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='outcome 1st peak')
DF['Candle +1 against trade 1st peak']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='Candle +1 against trade 1st peak')
DF['divergence 1st peak']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='divergence 1st peak')
DF['entry on RSI 1st peak']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='entry on RSI 1st peak')
DF['divergence 2nd peak']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='divergence 2nd peak')
DF['outcome 2nd peak']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='outcome 2nd peak')

# cleaning the n.a. values

DF["No of candles 1st peak"].fillna(0, inplace=True)
DF["bounce length 1st peak"].fillna(0, inplace=True)

def in_RSIarea(x):
    '''
    Function to check if the RSI indicator value is in overbought/oversold region
    
    Parameters
    ----------
    x = number representing the RSI value
        
    Returns
    -------
    1 if value is in overbought/oversold
    0 otherwise
    '''
   
    if x>=70 or x<=30: 
        return 1
    else:
        return 0

DF['rsi_inarea_1st']=DF['RSI 1st peak'].apply(in_RSIarea)

def sum_lengths(x):
    '''
    Function to calculate the sum (in number of candles)
    of all the RSI bounces
    
    Parameters
    ----------
    x = string with a comma separated list of numbers
        i.e. 1,4,2,3
        
    Returns
    -------
    An integer representing the total bounce length
    '''
    
    return sum([int(i) for i in x.split(",")])

DF['sum_bounces']=DF['bounce length 1st peak'].astype(str).apply(sum_lengths)

def calculate_points(row,attribs,verbose=str_to_bool(args.verbose)):
    '''
    Function to calculate the points for a particular trade
    
    Parameters
    ----------
    row : dataframe row
    attribs : list of dicts
              The dict has the following format:
              {'attr' : 'RSI bounces',
               'cutoff' : [(0,6), (7,10), (11,100000)],
               'points' : [2,-2,-3]}
    verbose : bool
              If true then print information on the contribution
              to the final score for each of the variables
               
    Returns
    -------
    Returns a score for this trade
    
    '''

    print("Processing: {0}".format(row['id 1st peak']))
    score=0
    for a in attribs:
        value=row[a]
        cutoffs=attribs[a]['intervals']
        points=attribs[a]['points']
        if len(cutoffs)!= len(points):
                raise Exception("Length of cutoffs is different to length of points for attrib:{0}".format(a))
        for i, j in zip(cutoffs, points):
            if j is None: j=0
            if isinstance(i[0], numbers.Number):
                upper=int(float(i[0]))
                lower=int(float(i[1]))
            else:
                upper=i[0]
                lower=i[1]
            if upper==lower:
                if value ==upper:
                    if verbose is True: print("{0} with a value of {1}, contributes with {2} points".format(a,value,j))
                    score+=j
                    continue
            else:
                iv = pd.Interval(left=upper, right=lower)
                if value in iv:
                    if verbose is True: print("{0} with a value of {1}, contributes with {2} points".format(a,value,j))
                    score+=j
                    continue
                
                
    return score

# Now, let's apply the calculate_points on each row for the training and the test set
DF['score']=DF.apply(calculate_points, axis=1, attribs=data)

outfile="{0}.{1}.tsv".format(args.prefix,args.timeframe)
DF.to_csv(outfile, sep='\t')

for index, row in DF.iterrows():
   print(row['id 1st peak']+"\t"+str(row['score']))

