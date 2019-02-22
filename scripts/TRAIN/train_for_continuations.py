# coding: utf-8
# author: ernesto lowy
# email: ernestolowy@gmail.com

import matplotlib
matplotlib.use('PS')
import pandas as pd
import numpy as np
import pdb
import re
import argparse
import os
import pdb
import math
import json
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
parser.add_argument('--prefix', default=False, required=True, help='Prefix for serialized JSON file')

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

# Calculate win-rate
print(DF[args.outcome].value_counts(normalize=True))


def calculate_points(v,cutoff,point_cutoff1,point_cutoff2):
    '''
    Function to calculate the number of points
    assigned to a particular interval/value

    Parameters
    ----------
    v: dict
       Containing information on the percentage for the two outcome categories
    cutoff : integer
             Only intervals for which either of the outcome percentanges is >=
             this cutoff
    point_cutoff1 : integer
                   1st cutoff used for deciding the point assignation. Default=5
    point_cutoff2 : integer
                   2nd cutoff used for deciding the point assignation. Default=10
    

    Returns
    -------
    integer representing the number of points
    assigned
    '''
    
    if len(v)<2:
        return 0
    outcomeA=v[0][args.outcome]
    percA=v[0]['percentage']
    outcomeB=v[1][args.outcome]
    percB=v[1]['percentage']
    if percA>=cutoff or percB>=cutoff:
        diff=abs(percA-percB)
        if outcomeA==1 and percA>percB:
            if 0 <= diff <= point_cutoff1:
                return 1
            elif point_cutoff1 <= diff <= point_cutoff2:
                return 2
            elif diff > point_cutoff2:
                return 3
        elif outcomeA==1 and percA<percB:
            if 0 <= diff <= point_cutoff1:
                return -1
            elif point_cutoff1 <= diff <= point_cutoff2:
                return -2
            elif diff > point_cutoff2:
                return -3
        elif outcomeA==0 and percA>percB:
            if 0 <= diff <= point_cutoff1:
                return -1
            elif point_cutoff1 <= diff <= point_cutoff2:
                return -2
            elif diff > point_cutoff2:
                return -3
        elif outcomeA==0 and percA<percB:
            if 0 <= diff <= point_cutoff1:
                return 1
            elif point_cutoff1 <= diff <= point_cutoff2:
                return 2
            elif diff > point_cutoff2:
                return 3
    else:
        return 0

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

def binning_plot(var,step,cutoff=10,point_cutoff1=5,point_cutoff2=10):
    '''
    Function to bin the numerical variable and create a barplot
    grouped by the outcome

    Parameters
    ----------
    var : string
           Variable name for calculating basic stats
    step : integer
           Step size for custom bins
    cutoff : integer
             Only intervals for which either of the outcome percentanges is >=
             this cutoff. Default = 10
    point_cutoff1 : integer
                   1st cutoff used for deciding the point assignation. Default=5
    point_cutoff2 : integer
                   2nd cutoff used for deciding the point assignation. Default=10

    Returns
    -------
    dict   Dict containing the intervals and points for each interval
    '''
    max_v=max(DF[var])

    custom_bins_array = np.arange(0, max_v, step)

    DF[var+"_cat"]=pd.cut(DF[var], np.around(custom_bins_array))
    
    DF_counts = (DF.groupby([args.outcome])[var+'_cat']
                 .value_counts(normalize=True)
                 .rename('percentage')
                 .mul(100)
                 .reset_index()
                 .sort_values(by=[var+'_cat']))

    print("##\n## {0}:\n##".format(var))
    print(tabulate(DF_counts, headers='keys', tablefmt='psql'))

    a = dict(DF_counts.set_index(var+'_cat').groupby(level = 0).\
    apply(lambda x : x.to_dict(orient= 'records')))
    intervals=[]
    points=[]
   
    for k in sorted(a.keys()):
        v=a[k]
        intervals.append([k.left,k.right])
        points.append(calculate_points(v,cutoff,point_cutoff1,point_cutoff2))

    a={'intervals': intervals,
       'points' : points}
        
    return a

#    sns.set(rc={'figure.figsize':(25,9)})
#    p = sns.barplot(x=var+"_cat", y="percentage", data=DF_counts)

#    fig=p.get_figure()
#    fig.savefig(var+".png")

def generate_barplot(var,cutoff=10,point_cutoff1=5,point_cutoff2=10):
    '''
    Function to create a normalized barplot

    Parameters
    ----------
    var : string
           Variable name for calculating basic stats
    cutoff : integer
             Only intervals for which either of the outcome percentanges is >=
             this cutoff. Default = 10
    point_cutoff1 : integer
                   1st cutoff used for deciding the point assignation. Default=5
    point_cutoff2 : integer
                   2nd cutoff used for deciding the point assignation. Default=10

    Returns
    -------
    dict   Dict containing the intervals and points for each interval
    '''
    DF_counts = (DF.groupby([args.outcome])[var]
                 .value_counts(normalize=True)
                 .rename('percentage')
                 .mul(100)
                 .reset_index()
                 .sort_values(var))

    print("##\n## {0}:\n##".format(var))
    print(tabulate(DF_counts, headers='keys', tablefmt='psql'))

    a = dict(DF_counts.set_index(var).groupby(level = 0).\
    apply(lambda x : x.to_dict(orient= 'records')))
        
    intervals=[]
    points=[]
    for k in sorted(a.keys()):
        v=a[k]
        intervals.append([k,k])
        points.append(calculate_points(v,cutoff,point_cutoff1,point_cutoff2))

    a={'intervals': intervals,
       'points' : points}
    
    return a
#    sns.set(rc={'figure.figsize':(25,9.27)})

#    p = sns.barplot(x=var, y="percentage", hue=args.outcome, data=DF_counts)

#    fig=p.get_figure()
#    fig.savefig(var+".png")

def calc_proportions(var,ref_cat,point_cutoff1=20, point_cutoff2=30):
    '''
    Function to calculate percentages of 'var' grouped by outcome

    Parameters
    ----------
    ref_cat : str
              Label for category that will be considered as the reference
    point_cutoff1 : integer
                   1st cutoff used for deciding the point assignation. Default=20
    point_cutoff2 : integer
                   2nd cutoff used for deciding the point assignation. Default=30

    Returns
    -------
    dict   Dict containing an interval and its points
    '''
    DF[var].value_counts()

    div_class=pd.crosstab(DF.iloc[:,outcome_ix], DF[var],margins=True)
    prop=(div_class/div_class.loc["All"])*100
    # get a list of columns
    cols = list(prop)

    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index(ref_cat)))

    # use ix to reorder
    prop = prop.ix[:, cols]

        
    print("##\n## {0}:\n##".format(var))
    print(tabulate(prop, headers='keys', tablefmt='psql'))

    diffs=[]
    intervals=[]
    prop_dict=prop.to_dict()
    ref_seen=False
    for k in cols:
        if k=="All": continue
        diffs.append(prop_dict[k][1]-prop_dict[k][0])
        if ref_seen==False:
            ref_seen=True
            continue
        else:
            intervals.append([k,k])

    ref=diffs[0]

    final_diffs=[]
    for i in range(1, len(diffs)):
        final_diffs.append(diffs[i]-ref)

    points=[]
    for d in final_diffs:
        if 0 <= d <= point_cutoff1:
            points.append(2)
        elif point_cutoff1 <= d <= point_cutoff2:
            points.append(3)
        elif d > point_cutoff2:
            points.append(5)

    a={'intervals': intervals,
       'points' : points}
    
    return a

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
    'length in pips (-1)' : 2000,
    'norm_length_pips' : 50,
    'pips_ratio' : 100,
    'pips_ratio_norm' :2,
    'inn_bounce' : 2,
    'sum_bounces' : 2,
    'bounce (pips)' : 500,
    'norm_bounce_pips' : 10,
    'bounce_ratio' : 2
    }

final_dict={}
for v in ['diff','length of trend (-1)', 'length_bounce_perc', 'length in pips (-1)',
          'norm_length_pips','pips_ratio', 'pips_ratio_norm', 'inn_bounce', 'sum_bounces', 'bounce (pips)',
          'norm_bounce_pips','bounce_ratio']:
    stats_table(v)
    final_dict[v]=binning_plot(v, step_s[v])

#
# Generate Barplots
#
for v in ['RSI bounces','trend_bounces','s_r_bounces','peak_bounces','indecission']:
    stats_table(v)
    final_dict[v]=generate_barplot(v)

#
# Calculate proportions
#
for v in ['entry on RSI','entry_aligned','bounce_bias']:
    if v=='bounce_bias':
        final_dict[v]=calc_proportions(v,'P')
    else:
        final_dict[v]=calc_proportions(v,0)

outfile="{0}.{1}.json".format(args.prefix,args.timeframe)

with open(outfile, "w") as write_file:
    json.dump(final_dict,
              write_file,
              sort_keys=True,
              indent=4)    

