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
import math
import seaborn as sns
from tabulate import tabulate

from sklearn.preprocessing import Imputer
from prettytable import PrettyTable


parser = argparse.ArgumentParser(description='This script is used with training data in order to assess the points assigned to each of the variables')

parser.add_argument('--ifile', required=True, help='input file containing the training trades. Valid formats are .csv or .tsv')
parser.add_argument('--timeframe', required=True, help='Input dataframe. Valid values are: ALL,D,H12,H6')
parser.add_argument('--outcome', required=True, help='outcome type. Possible values are outcome or ext_outcome')
parser.add_argument('--print_sorted', default=False, required=False, help='Print sorted (by date) .tsv')
parser.add_argument('--entry_aligned', default=False, required=False, help='If true, then consider only trades having entry_aligned=1')

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

#read-in the data
DF=pd.read_csv(args.ifile,sep=separator,na_values=["n.a.","n.a"])

print("Total # of records: {0}; # of variables: {1}".format(DF.shape[0], DF.shape[1]))

if not args.timeframe in ['ALL','D','H12','H8','H4']:
    raise Exception("{0} timeframe is not valid".format(args.timeframe))

if args.timeframe != 'ALL':
    DF=DF[DF['timeframe']==args.timeframe]

print("Total # of records for desired timeframe: {0}; # of variables: {1}".format(DF.shape[0], DF.shape[1]))

if str_to_bool(args.entry_aligned) is True:
    DF=DF.loc[DF['entry_aligned']==1]
    print("Total # of records after discarding entry_aligned=0: {0}; # of variables: {1}".format(DF.shape[0], DF.shape[1]))
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

#
# Calculate ext outcome
#

def calc_extoutcome(row,cutoff=20):
    if not math.isnan(row['norm_retraced']):
        if row['norm_retraced']<=cutoff:
            return int(1)
        else:
            return int(0)
    else:
        return int(row['outcome'])

DF['ext_outcome']=DF.apply(calc_extoutcome,axis=1)
outcome_ix=DF.columns.values.tolist().index(args.outcome)

def stats_table(var):
    '''
    Function to calculate the mean,median grouped by the outcome

    Parameters
    ----------
    var : string
          Variable name for calculating basic stats
    '''
    res_mean=DF.groupby(args.outcome).agg({ var : 'mean'})
    res_mean.columns=['mean']

    res_median=DF.groupby(args.outcome).agg({ var : 'median'})
    res_median.columns=['median']

    res_f=pd.merge(res_mean,res_median,left_index=True, right_index=True)

    print("##\n## {0}:\n##".format(var))
    print(tabulate(res_f, headers='keys', tablefmt='psql'))

def binning_plot(var,step):
    '''
    Function to bin the numerical variable and create a barplot
    grouped by the outcome

    Parameters
    ----------
    var : string
           Variable name for calculating basic stats
    step : integer
           Step size for custom bins
    '''
    max_v=max(DF[var])

    custom_bins_array = np.arange(0, max_v, step)

    DF[var+"_cat"]=pd.cut(DF[var], np.around(custom_bins_array))

    DF_counts = (DF.groupby([args.outcome])[var+'_cat']
                 .value_counts(normalize=True)
                 .rename('percentage')
                 .mul(100)
                 .reset_index()
                 .sort_values(var+'_cat'))

    sns.set(rc={'figure.figsize':(25,9)})

    p = sns.barplot(x=var+"_cat", y="percentage", hue=args.outcome, data=DF_counts)

    fig=p.get_figure()
    fig.savefig(var+".png")

def generate_barplot(var):
    '''
    Function to create a normalized barplot

    Parameters
    ----------
    var : string
           Variable name for calculating basic stats
    '''
    DF_counts = (DF.groupby([args.outcome])[var]
                 .value_counts(normalize=True)
                 .rename('percentage')
                 .mul(100)
                 .reset_index()
                 .sort_values(var))

    sns.set(rc={'figure.figsize':(25,9.27)})

    p = sns.barplot(x=var, y="percentage", hue=args.outcome, data=DF_counts)

    fig=p.get_figure()
    fig.savefig(var+".png")

def calc_proportions(var):
    '''
    Function to calculate percentages of 'var' grouped by outcome
    '''
    
    DF[var].value_counts()

    div_class=pd.crosstab(DF.iloc[:,outcome_ix], DF[var],margins=True)
    prop=(div_class/div_class.loc["All"])*100
    print("##\n## {0}:\n##".format(var))
    print(tabulate(prop, headers='keys', tablefmt='psql'))

#
# last time 
# This datetime variable represents the last time the price was over/below the entry price level.
# The first to do is to create a new datetime variable representing the difference (in days) between
# the entry datetime (start column) and the last time datetime

DF['diff']=(DF['start']-DF['last time'])
DF['diff']=DF['diff'].apply(lambda x: x.days)

#
# length_bounce_perc
# This variable represents what % of the total length of the trend represents the inn_bounce
DF['length_bounce_perc']=DF['inn_bounce'].astype(int)*100/DF['length of trend (-1)'].astype(int)

# ### Pips_ratio
# This variable contains the ratio between 'length in pips'/'length of trend (-1)'
DF['pips_ratio']=DF['length in pips (-1)'].astype(int)/DF['length of trend (-1)'].astype(int)

### Pips_ratio normalized
DF['pips_ratio_norm']=DF['norm_length_pips'].astype(int)/DF['length of trend (-1)'].astype(int)

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

#
# Calculate basic stats and binning plots
#

step_s={
    'diff' : 150,
    'length of trend (-1)' : 10,
    'length_bounce_perc' : 10,
    'length in pips (-1)' :2000,
    'pips_ratio' : 100,
    'pips_ratio_norm' :2,
    'inn_bounce' : 2,
    'sum_bounces' : 2,
    'bounce (pips)' : 500,
    'norm_bounce_pips' : 10,
    'bounce_ratio' : 2
    }

for v in ['diff','length of trend (-1)', 'length_bounce_perc', 'length in pips (-1)',
          'pips_ratio', 'pips_ratio_norm', 'inn_bounce', 'sum_bounces', 'bounce (pips)',
          'norm_bounce_pips','bounce_ratio']:
    stats_table(v)
    binning_plot(v, step_s[v])

#
# Generate Barplots
#
for v in ['RSI bounces','trend_bounces','s_r_bounces','peak_bounces','indecission']:
    stats_table(v)
    generate_barplot(v)

#
# Calculate proportions
#
for v in ['entry on RSI','entry_aligned','bounce_bias']:
    calc_proportions(v)
    
