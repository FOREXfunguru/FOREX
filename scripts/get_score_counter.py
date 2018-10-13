import pandas as pd
import numpy as np
import pdb
import re
import seaborn as sns
from pandas.plotting import scatter_matrix
from sklearn.metrics import confusion_matrix,precision_score
from sklearn.model_selection import train_test_split

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

contDF=read_tradedata('/Users/ernesto/Downloads/Screenshot_analysis_counter.csv',sep=",",na_values=["n.a.","n.a"])

contDF['start']= pd.to_datetime(contDF['start'])
contDF['last time']= pd.to_datetime(contDF['last time'])

contDF["No of candles"].fillna(0, inplace=True)

contDF["bounce length"].fillna(0, inplace=True)

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
contDF['Candle +1 against trade']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='Candle +1 against trade')
contDF['entry on RSI']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='entry on RSI')
contDF['strong trend']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='strong trend')


outcome_ix=5 # 4=outcome and 5= ext_outcome
outcome_lab="ext_outcome"
contDF.iloc[:,outcome_ix].value_counts()

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
    
contDF['sum_bounces']=contDF['bounce length'].astype(str).apply(sum_lengths)


def avg_angle(x):
    '''
    Function to calculate the average angle for all the
    streches
    
    Parameters
    ----------
    x = string with a comma separated list of numbers
        i.e. 1,4,2,3
        
    Returns
    -------
    A float representing the average angle
    '''
    l=[int(i) for i in x.split(",")]
    mean=sum(l)/len(l)
    return mean
contDF['avg_angle']=contDF['stretches'].astype(str).apply(avg_angle)

def number_of_stretches(x):
    '''
    Function to calculate the number of streches
    
    Parameters
    ----------
    x = string with a comma separated list of numbers
        i.e. 1,4,2,3
        
    Returns
    -------
    An integeger
    '''
    
    return len([int(i) for i in x.split(",")])


# In[538]:


contDF['no_stretches']=contDF['stretches'].astype(str).apply(number_of_stretches)

def last_stretch(x):
    '''
    Function to calculate the angle of the last strech
    
    Parameters
    ----------
    x = string with a comma separated list of numbers
        i.e. 1,4,2,3
        
    Returns
    -------
    A float
    '''
    
    l=[int(i) for i in x.split(",")]
    
    return l[len(l)-1]

contDF['last_stretch']=contDF['stretches'].astype(str).apply(last_stretch)

contDF['diff']=(contDF['start']-contDF['last time'])

contDF['diff']=contDF['diff'].apply(lambda x: x.days)


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
            if a['rel'] == 'is_true_oneway':
                if value == True or value == 1:
                    score+=points
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
            elif a['rel'] == 'gt':
                if value >= cutoff: 
                    score+=points
                if value < cutoff: 
                    score+=-1*points
                
    return score

attbs=[]

attbs.append({
        'attr' : 'RSI bounces',
        'cutoff' : 4,
        'rel' : 'gt',
        'points' : 1
        })
attbs.append({
        'attr' : 'No of candles',
        'cutoff' : 10,
        'rel' : 'gt',
        'points' : 1
        })
attbs.append({
        'attr' : 'entry on RSI',
        'cutoff' : 'bool',
        'rel' : 'is_true_oneway',
        'points' : -3
        })
attbs.append( {
        'attr' : 'length of trend',
        'cutoff' : 65,
        'rel' : 'gt',
        'points' : 1
        })
attbs.append( {
        'attr' : 'divergence',
        'cutoff' : 'bool',
        'rel' : 'is_true_oneway',
        'points' : 3
        })
attbs.append( {
        'attr' : 'sum_bounces',
        'cutoff' : 7,
        'rel' : 'gt',
        'points' : 1
        })
attbs.append( {
        'attr' : 'bounces',
        'cutoff' : 2,
        'rel' : 'gt',
        'points' : 2
        })
attbs.append( {
        'attr' : 'avg_angle',
        'cutoff' : 30,
        'rel' : 'less',
        'points' : 1
        })
attbs.append( {
        'attr' : 'no_stretches',
        'cutoff' : 4,
        'rel' : 'gt',
        'points' : 2
        })
attbs.append( {
        'attr' : 'last_stretch',
        'cutoff' : 60,
        'rel' : 'less',
        'points' : 1
        })
attbs.append( {
        'attr' : 'diff',
        'cutoff' : 590,
        'rel' : 'gt',
        'points' : 1
        })

contDF['score']=contDF.apply(calculate_points, axis=1, attribs=attbs)

for index, row in contDF.iterrows():
   print(row['id']+"\t"+str(row['score']))
