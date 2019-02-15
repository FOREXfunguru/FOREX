# coding: utf-8
# author: ernesto lowy
# email: ernestolowy@gmail.com

import pandas as pd
import numpy as np
import pdb
import re
import argparse
import os
import pdb

from sklearn.preprocessing import Imputer

parser = argparse.ArgumentParser(description='This script is used with training data in order to assess the points assigned to each of the variables')

parser.add_argument('--ifile', required=True, help='input file containing the training trades. Valid formats are .csv or .tsv')
parser.add_argument('--timeframe', required=True, help='Input dataframe. Valid values are: ALL,D,H12,H6')
parser.add_argument('--verbose', required=True, help='Increase verbosity')
args = parser.parse_args()

ext=os.path.splitext(args.ifile)[1]

separator=None
if ext == '.tsv':
    separator="\t"
elif ext == '.csv':
    separator=","
else:
    raise Exception("Extension {0} is not recognized".format(ext))

#read-in the data
DF=pd.read_csv(args.ifile,sep=separator,na_values=["n.a.","n.a"])

print("Total # of records: {0}; # of variables: {1}".format(DF.shape[0], DF.shape[1]))

if not args.timeframe in ['ALL','D','H12','H8','H4']:
    raise Exception("{0} timeframe is not valid".format(args.timeframe))

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

for v in ['length in pips (-1)','bounce (pips)','retraced']:
    DF[v]=DF.apply(normalize,axis=1, variable_name=v)

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

if "ext_outcome" in DF: DF['ext_outcome']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='ext_outcome')
DF['outcome']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='outcome')
DF['entry on RSI']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='entry on RSI')
if "strong_trend" in DF: DF['strong trend']=DF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='strong trend')

if args.print_sorted==True:
    # Sort the trades by date to check if there are reduntant trades:
    sortedDF= DF.sort_values(by='start')
    sortedDF.to_csv('sorted_contDF.tsv',sep='\t')
    
pdb.set_trace()
    
print("h\n")
