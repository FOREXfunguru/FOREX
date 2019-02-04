
# coding: utf-8

import pandas as pd
import numpy as np
import pdb
import re
import argparse

parser = argparse.ArgumentParser(description='Script to calculate the score for continuation trades')

parser.add_argument('--DF', required=True, help='input dataframe')
parser.add_argument('--timeframe', required=True, help='Input dataframe. Valid values are: ALL,D,H12,H6')
parser.add_argument('--verbose', required=True, help='Increase verbosity')
args = parser.parse_args()

def str_to_bool(s):
    if s == 'True' or s=='true':
         return True
    elif s == 'False' or s== 'false':
         return False
    else:
         raise ValueError

def read_tradedata(tradefile,sep,na_values):
    '''
    Parameters
    ----------
    tradefile : str, required
                Path to file containing the trade data
    sep : str, optionsl
          Field separator used in the file. i.e. ',' (comma separated values), '\t' (tab-separated values)
    na_values : list, optional
                Additional list of strings to recognize as NA/NaN. i.e. ['n.a.']
    
    Returns
    -------
    A Pandas dataframe
    '''
    DF=pd.read_csv(tradefile,sep=sep,na_values=na_values)
    
    return DF

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

# read-in the data
contDF=read_tradedata(args.DF,sep="\t",na_values=["n.a.","n.a"])

# convert to datetime
contDF['start']= pd.to_datetime(contDF['start'])
contDF['last time']= pd.to_datetime(contDF['last time'])

# cleaning the n.a. values
contDF["bounce length"].fillna(0, inplace=True)
contDF["length of trend (-1)"].fillna(0, inplace=True)
contDF["length in pips (-1)"].fillna(0, inplace=True)

# normalizing the pips pased variables
contDF['norm_length_pips']=contDF.apply(normalize,axis=1, variable_name='length in pips (-1)')
contDF['norm_bounce_pips']=contDF.apply(normalize,axis=1, variable_name='bounce (pips)')

# transforming categorical binary variables
contDF['outcome']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='outcome')
contDF['entry on RSI']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='entry on RSI')

# selecting the desired dataframe
if args.timeframe!='ALL' and args.timeframe!='ALL_entry':
    contDF=contDF[contDF.timeframe == args.timeframe]

outcome_ix=6 # 4=outcome and 5= ext_outcome
outcome_lab="outcome"

#calculating diff variable 
contDF['diff']=(contDF['start']-contDF['last time'])
contDF['diff']=contDF['diff'].apply(lambda x: x.days)

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
    if x=='0.0':
        return 0
    else:
        return sum([int(i) for i in x.split(",")])
    

contDF['sum_bounces']=contDF['bounce length'].astype(str).apply(sum_lengths)
contDF['pips_ratio']=contDF['length in pips (-1)'].astype(int)/contDF['length of trend (-1)'].astype(int)
contDF['bounce_ratio']=contDF['inn_bounce']/contDF['indecission']
verbose=str_to_bool(args.verbose)


def calculate_points(row,attribs,verbose=verbose):
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
        attrb_name=a['attr']
        value=row[a['attr']]
        cutoffs=a['cutoffs']
        points=a['points']
        if cutoffs =='bool':
            if a['rel'] == 'is_true':
                if value == True or value == 1:
                    if verbose is True: print("{0} contributes with {1} points".format(attrb_name,points))
                    score+=points
                if value == False  or value == 0:
                    if verbose is True: print("{0} contributes with -{1} points".format(attrb_name,points))
                    score+=-1*points
        else:
            if len(cutoffs)!= len(points):
                raise Exception("Length of cutoffs is different to length of points")
            for i, j in zip(cutoffs, points):
                if value>=i[0] and value<=i[1]:
                    if verbose is True: print("{0} with a value of {1}, contributes with {2} points".format(attrb_name,value,j))
                    score+=j
                
    return score

attbs=[]

if args.timeframe=='ALL_entry':
    attbs.append({
        'attr' : 'diff',
        'cutoffs' : [(0,700),(701,100000)],
        'points' : [1,-1]
        })
    attbs.append({
        'attr' : 'RSI bounces',
        'cutoffs' : [(0,0),(1,3),(4,100000)],
        'points' : [1,2,-2]
        })
    attbs.append({
        'attr' : 'entry on RSI',
        'cutoffs' : 'bool',
        'rel' : 'is_true',
        'points' : 1
        })
    attbs.append({
        'attr' : 'length of trend (-1)',
        'cutoffs' : [(0,10),(11,40),(41,50),(51,120),(121,10000)],
        'points' : [-1,2,1,-1,-2]
        })
    attbs.append( {
        'attr' : 'sum_bounces',
        'cutoffs' : [(0,3),(4,100000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'norm_bounce_pips',
        'cutoffs' : [(0,48),(49,1000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'indecission',
        'cutoffs' : [(0,1),(1,2),(3,3),(4,1000)],
        'points' : [-1,2,-1,-2]
        })
elif args.timeframe=='ALL':
    attbs.append({
        'attr' : 'diff',
        'cutoffs' : [(0,700),(701,100000)],
        'points' : [1,-1]
        })
    attbs.append({
        'attr' : 'RSI bounces',
        'cutoffs' : [(0,2), (3,3), (4,100000)],
        'points' : [2,-1,-2]
        })
    attbs.append({
        'attr' : 'entry on RSI',
        'cutoffs' : 'bool',
        'rel' : 'is_true',
        'points' : 3
        })
    attbs.append({
        'attr' : 'length of trend (-1)',
        'cutoffs' : [(0,10),(11,25),(26,35),(36,60),(61,10000)],
        'points' : [-1,2,1,-1,-2]
        })
    attbs.append( {
        'attr' : 'inn_bounce',
        'cutoffs' : [(0,7),(8,1000000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'pips_ratio_norm',
        'cutoffs' : [(0,3),(4,30)],
        'points' : [-2,2]
        })
    attbs.append( {
        'attr' : 'sum_bounces',
        'cutoffs' : [(0,7),(8,100000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'norm_bounce_pips',
        'cutoffs' : [(0,48),(49,1000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'entry_aligned',
        'cutoffs' : 'bool',
        'rel' : 'is_true',
        'points' : 6
        })
    attbs.append( {
        'attr' : 'indecission',
        'cutoffs' : [(0,3),(4,5),(6,100)],
        'points' : [1,-1,-2]
        })
    attbs.append( {
        'attr' : 'bounce_ratio',
        'cutoffs' : [(0,3),(4,10000)],
        'points' : [-2,2]
        })
elif args.timeframe=='D':
    attbs.append({
        'attr' : 'diff',
        'cutoffs' : [(0,300),(301,100000)],
        'points' : [2,-2]
        })
    attbs.append({
        'attr' : 'RSI bounces',
        'cutoffs' : [(0,2), (3,3), (4,100000)],
        'points' : [2,-1,-2]
        })
    attbs.append({
        'attr' : 'entry on RSI',
        'cutoffs' : 'bool',
        'rel' : 'is_true',
        'points' : 3
        })
    attbs.append( {
        'attr' : 'length of trend (-1)',
        'cutoffs' : [(0,10),(11,14),(15,23),(24,50),(51,10000)],
        'points' : [-1,1,2,1,-2]
        })
    attbs.append( {
        'attr' : 'inn_bounce',
        'cutoffs' : [(0,7),(8,1000000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'pips_ratio',
        'cutoffs' : [(0,150),(151,220),(221,1000000000000)],
        'points' : [-2,1,2]
        })
    attbs.append( {
        'attr' : 'sum_bounces',
        'cutoffs' : [(0,6),(7,1000000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'bounce (pips)',
        'cutoffs' : [(0,800),(801,1000000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'entry_aligned',
        'cutoffs' : 'bool',
        'rel' : 'is_true',
        'points' : 6
        })
    attbs.append( {
        'attr' : 'indecission',
        'cutoffs' : [(0,3),(4,20)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'bounce_ratio',
        'cutoffs' : [(0,4),(5,10000)],
        'points' : [-2,2]
        })
elif args.timeframe=='H12':
    attbs.append({
        'attr' : 'diff',
        'cutoffs' : [(0,600),(601,100000)],
        'points' : [2,-2]
        })
    attbs.append({
        'attr' : 'RSI bounces',
        'cutoffs' : [(0,1),(2,2),(3,6),(7,100000)],
        'points' : [2,1,-1,-2]
        })
    attbs.append({
        'attr' : 'entry on RSI',
        'cutoffs' : 'bool',
        'rel' : 'is_true',
        'points' : 3
        })
    attbs.append( {
        'attr' : 'length of trend (-1)',
        'cutoffs' : [(0,9), (10,99),(100,1000000)],
        'points' : [-1,1,-1]
        })
    attbs.append( {
        'attr' : 'inn_bounce',
        'cutoffs' : [(0,7),(8,1000000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'pips_ratio',
        'cutoffs' : [(0,150),(151,1000000000000)],
        'points' : [-2,2]
        })
    attbs.append( {
        'attr' : 'sum_bounces',
        'cutoffs' : [(0,4),(5,100000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'bounce (pips)',
        'cutoffs' : [(0,900),(901,1000000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'entry_aligned',
        'cutoffs' : 'bool',
        'rel' : 'is_true',
        'points' : 6
        })
    attbs.append( {
        'attr' : 'indecission',
        'cutoffs' : [(0,5),(6,20)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'bounce_ratio',
        'cutoffs' : [(0,6),(7,10000)],
        'points' : [2,-2]
        })
elif args.timeframe=='H6':
    attbs.append({
        'attr' : 'diff',
        'cutoffs' : [(0,350),(351,1000000)],
        'points' : [-2,2]
        })
    attbs.append({
        'attr' : 'RSI bounces',
        'cutoffs' : [(0,0),(1,3),(4,1000)],
        'points' : [-1,2,-1]
        })
    attbs.append({
        'attr' : 'entry on RSI',
        'cutoffs' : 'bool',
        'rel' : 'is_true',
        'points' : 3
        })
    attbs.append( {
        'attr' : 'inn_bounce',
        'cutoffs' : [(0,5),(6,1000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'pips_ratio',
        'cutoffs' : [(0,100),(101,10000)],
        'points' : [-1,1]
        })
    attbs.append( {
        'attr' : 'sum_bounces',
        'cutoffs' : [(0,3),(4,100000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'bounce (pips)',
        'cutoffs' : [(0,600),(601,1000000)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'entry_aligned',
        'cutoffs' : 'bool',
        'rel' : 'is_true',
        'points' : 6
        })
    attbs.append( {
        'attr' : 'indecission',
        'cutoffs' : [(0,1),(2,10)],
        'points' : [2,-2]
        })
    attbs.append( {
        'attr' : 'bounce_ratio',
        'cutoffs' : [(0,5),(6,1000)],
        'points' : [-2,2]
        })

# Now, let's apply the calculate_points on each row for the training and the test set

contDF['score']=contDF.apply(calculate_points, axis=1, attribs=attbs)

for index, row in contDF.iterrows():
   print(row['id']+"\t"+str(row['score']))
