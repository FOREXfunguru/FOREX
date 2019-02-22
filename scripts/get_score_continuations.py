
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

parser = argparse.ArgumentParser(description='Script to calculate the score for continuation trades')

parser.add_argument('--ifile', required=True, help='input file containing the training trades. Valid formats are .csv or .tsv')
parser.add_argument('--timeframe', required=True, help='Input dataframe. Valid values are: ALL,D,H12,H6')
parser.add_argument('--attrbs', required=True, help='Json file calculated by train_for_continuations.py')
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

#
# Convert to datetime the relevant variables
#
for v in ['start','last time']:
    DF[v]= pd.to_datetime(DF[v])

#
# Impute missing values for some variables
#

def impute_missing_values(data, strat):
    '''
    Impute missing values with the strategy passed with 'strat'.

    Parameters
    ----------
    data : pandas series
    strat : string
            What strategy will the Imputer use. For example: 'mean','median'

    Returns
    -------
    A Pandas DF that will have 'var' imputed
    '''
    
    imputer = Imputer(strategy=strat)
    imputer.fit(data.values.reshape(-1, 1))
    X = imputer.transform(data.values.reshape(-1,1))
    
    return X

for v in ['length of trend (-1)', 'length in pips (-1)', 's_r_bounces', 'peak_bounces']:
    DF[v]=impute_missing_values(DF[v],strat='median')

#
# Normalize the pips variables

def normalize(x, variable_name):
    '''
    Function that will calculate the number of pips per hour
    
    Parameters
    ----------
    variable: str
              Variable name that will be normalized
    '''
    
    return round(x[variable_name]/48,2)
    
    if x['timeframe']=='2D':
        return round(x[variable_name]/48,1)
    elif x['timeframe']=='D':
        return round(x[variable_name]/24,1)
    elif x['timeframe']=='H12':
        return round(x[variable_name]/12,1)
    elif x['timeframe']=='H10':
        return round(x[variable_name]/10,1)
    elif x['timeframe']=='H8':
        return round(x[variable_name]/8,1)
    elif x['timeframe']=='H6':
        return round(x[variable_name]/6,1)
    else:
        raise("Error")

DF['norm_length_pips']=DF.apply(normalize,axis=1, variable_name='length in pips (-1)')
DF['norm_bounce_pips']=DF.apply(normalize,axis=1, variable_name='bounce (pips)')
DF['norm_retraced']=DF.apply(normalize,axis=1, variable_name='retraced')

#
# last time 
# This datetime variable represents the last time the price was over/below the entry price level.
# The first to do is to create a new datetime variable representing the difference (in days) between
# the entry datetime (start column) and the last time datetime

DF['diff']=(DF['start']-DF['last time'])
DF['diff']=DF['diff'].apply(lambda x: x.days)

# ### Pips_ratio
# This variable contains the ratio between 'length in pips'/'length of trend (-1)'
DF['pips_ratio']=DF['length in pips (-1)'].astype(int)/DF['length of trend (-1)'].astype(int)

### Pips_ratio normalized
DF['pips_ratio_norm']=DF['norm_length_pips'].astype(int)/DF['length of trend (-1)'].astype(int)

# length_bounce_perc
# This variable represents what % of the total length of the trend represents the inn_bounce
DF['length_bounce_perc']=DF['inn_bounce'].astype(int)*100/DF['length of trend (-1)'].astype(int)

### bounce_bias
# This is a derived categorical variable named `bounce_bias` that will be `P` if there are more peak bounces than S/R bounces,
# `A` if there are more bounces at the S/R area than at the peak and `U` if there is the same number of bounces at the 2 areas. 

def calc_bounce_bias(row):
    '''
    Function to calculate the value of bounce_bias
    '''
    s_r_bounces=row['s_r_bounces']
    peak_bounces=row['peak_bounces']
    
    if s_r_bounces > peak_bounces:
        return 'A'
    elif s_r_bounces < peak_bounces:
        return 'P'
    elif s_r_bounces == peak_bounces:
        return 'U'

DF['bounce_bias']=DF.apply(calc_bounce_bias,axis=1)

### Inn_bounce/Indecisison ratio
# Float variable representing the ratio between the internal bounce divided by the indecission ratio
DF['bounce_ratio']=DF['inn_bounce']/DF['indecission']

### bounce length
# This variable is a comma separated list of integers representing how wide (in number of candles) each of the RSI bounces is. This variable requires a little bit of preprocessing, and I will write a f# unction that calculates the total length (in number of candles) by adding the length of each of the bounces

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

# Replace n.a. by 0s
DF["bounce length"].fillna(0, inplace=True)
DF['sum_bounces']=DF['bounce length'].astype(str).apply(sum_lengths)

#
# Transforming categorical binary variables into 1s and 0s
#

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

DF['outcome']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='outcome')
DF['entry on RSI']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='entry on RSI')
if "strong_trend" in DF: DF['strong trend']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='strong trend')

def calculate_points(row,attribs,verbose=args.verbose):
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
    score=0
    for a in attribs:
        if a=="bounce_bias":
            print("h\n")
            pdb.set_trace()
        value=row[a]
        cutoffs=attribs[a]['intervals']
        points=attribs[a]['points']
        if len(cutoffs)!= len(points):
                raise Exception("Length of cutoffs is different to length of points")
        for i, j in zip(cutoffs, points):
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
            else:
                iv = pd.Interval(left=upper, right=lower)
                if value in iv:
                    if verbose is True: print("{0} with a value of {1}, contributes with {2} points".format(a,value,j))
                    score+=j
                
                
    return score

# Now, let's apply the calculate_points on each row for the training and the test set
DF['score']=DF.apply(calculate_points, axis=1, attribs=data)

for index, row in contDF.iterrows():
   print(row['id']+"\t"+str(row['score']))
