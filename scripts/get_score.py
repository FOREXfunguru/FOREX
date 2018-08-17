"""
author: ernesto.lowy@gmail.com

This script will take a .csv file containing a set of trades with some features associated that are considered to be related to the trade outcome
and will calculate a score for this particular trade
"""
import pandas as pd
import pdb
import re

def calculate_points(row,attribs):
    '''
    Function to calculate the points for a particular trade
    
    Parameters
    ----------
    row : dataframe row
    attribs : list of dicts
              The dict has the following format:
              {'attr' : 'RSI bounces',
               'cutoff' : 3,
               'points' : 2}
               
    Returns
    -------
    Returns a score for this trade
    
    '''
    score=0
    for a in attribs:
        value=row[a['attr']]
        cutoff=a['cutoff']
        points=a['points']
        if cutoff =='bool':
            if a['rel'] == 'is_true':
                if value == True:
                    score+=points
                if value == False:
                    score+=-1*points
        else:
            if a['rel'] == 'less':
                if value < cutoff: 
                    score+=points
                if value >= cutoff: 
                    score+=-1*points
            elif a['rel'] == 'range':
                p=re.compile("(\d+)-(\d+)")
                m=p.match(cutoff)
                upp=int(m.group(2))
                low=int(m.group(1))
                if value >=low and value <=upp:
                    score+=points
                else:
                    score+=-1*points
                
    return score

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
    


attbs=[]

attbs.append({
        'attr' : 'RSI bounces',
        'cutoff' : 5,
        'rel' : 'less',
        'points' : 2
        })
attbs.append( {
        'attr' : 'entry on RSI',
        'cutoff' : 'bool',
        'rel' : 'is_true',
        'points' : 1
        })
attbs.append( {
        'attr' : 'length of trend',
        'cutoff' : '15-70',
        'rel' : 'range',
        'points' : 1
        })
attbs.append( {
        'attr' : 'inn_bounce',
        'cutoff' : 13,
        'rel' : 'less',
        'points' : 1
        })
attbs.append( {
        'attr' : 'indecission',
        'cutoff' : 7,
        'rel' : 'less',
        'points' : 1
        })
attbs.append( {
        'attr' : 'strong trend',
        'cutoff' : 'bool',
        'rel' : 'is_true',
        'points' : 1
        })
attbs.append( {
        'attr' : 'sum_bounces',
        'cutoff' : 13,
        'rel' : 'less',
        'points' : 2
        })

pdb.set_trace()
contDF=read_tradedata('/Users/ernesto/Downloads/Screenshot analysis - only1row.csv',sep=",",na_values=["n.a.","n.a"])
contDF_dropna=contDF.dropna(subset=['bounce length'])
contDF_dropna['sum_bounces']=contDF_dropna['bounce length'].astype(str).apply(sum_lengths)


contDF_dropna['score']=contDF_dropna.apply(calculate_points, axis=1, attribs=attbs)

print("Score:{0}\n".format(contDF_dropna['score']))



