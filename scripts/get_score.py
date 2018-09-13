import pandas as pd
import numpy as np
import pdb
import re

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

contDF=read_tradedata('/Users/ernesto/Downloads/Screenshot analysis - only1row.csv',sep=",",na_values=["n.a.","n.a"])


# ## Cleaning the n.a. values
# The following predictors have n.a. values and the strategy I will follow will depend on each case:

# * Bounce length (will replace the n.a. by 0)

contDF["bounce length"].fillna(0, inplace=True)


# ## Transforming

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

contDF['ext_outcome']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='ext_outcome')
contDF['entry on RSI']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='entry on RSI')
contDF['strong trend']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='strong trend')

outcome_ix=5 # 4=outcome and 5= ext_outcome
outcome_lab="ext_outcome"

# For now I am not going to consider the trades having an outcome of 'B'. So, let's remove them from the dataframe:

contDF=contDF[contDF.outcome != 'B']

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
    


# And I will apply the `sum_lengths` function and put the results in a new column named `sum_bounces`

contDF['sum_bounces']=contDF['bounce length'].astype(str).apply(sum_lengths)

# ## Calculating points
# This section will calculate a total score for each trade that will be used to predict the outcome.<br>

# First, let's create a function to calculate the points

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
                if value == True or value == 1:
                    score+=points
                if value == False  or value == 0:
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

attbs=[]

attbs.append({
        'attr' : 'RSI bounces',
        'cutoff' : 5,
        'rel' : 'less',
        'points' : 2
        })
attbs.append({
        'attr' : 'entry on RSI',
        'cutoff' : 'bool',
        'rel' : 'is_true',
        'points' : 1
        })
attbs.append( {
        'attr' : 'length of trend',
        'cutoff' : '5-70',
        'rel' : 'range',
        'points' : 1
        })
attbs.append( {
        'attr' : 'inn_bounce',
        'cutoff' : 11,
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
        'cutoff' : 8,
        'rel' : 'less',
        'points' : 2
        })
attbs.append( {
        'attr' : 'bounce (pips)',
        'cutoff' : 3000,
        'rel' : 'less',
        'points' : 2
        })


# Now, let's apply the calculate_points on each row for the training and the test set

contDF['score']=contDF.apply(calculate_points, axis=1, attribs=attbs)

for index, row in contDF.iterrows():
   print(row['id']+"\t"+str(row['score']))
