
# coding: utf-8

# # Motivation
# This notebook analyses the spreadsheet containing information on the reversals. This spreadsheet collects different features on the trades in an attempt of creating a binary classifier, this classifier will learn from the data collected and will predict the value of the `outcome` variable, which can be success of failre
# 
# # Data
# The data has been collected in an spreadsheet containing trades both simulated and real. And the different trades have been classified into three types: continuation, counter and ranging. The independent variables gathered for each trade type are:
# ## Continuation trades
# * id	id used in the screenshot folder to identify this record
# * start	start of this trade
# * timeframe	in the format 2D,D,H12,H8
# * entry	price
# * outcome	S=success;F=failure;B=breakeven
# * ext_outcome. S=success;F=failure;B=breakeven
# * RSI bounces. number of RSI bounces ocurring in the trend before entry
# * No of candles. How many candles before occurred the bounce, from the entry of trade to the first bounce (without counting the entry candle)
# * entry on RSI. Was the entry candle on RSI?
# * length of trend. lenght of the preceding trend in number of candles. The valley before the continuation is not included in the count
# * previous swings. Number of swings from the entry and counting the rebound before the entry (see screenshot below)
# * space interswings. Comma separated numbers representing the number of candles between swings from the most recent to the oldest
# * length in pips. From the beginning of the trade to the entry price in number of pips
# strong trend	TRUE of the preceding trend was strong
# * trend angle. Measured with Oanda after hitting the auto scale button+lock scalde button and the end of the trend line is the IC+1 when it touches the entry price
# * bounce length. Length in number of candles for each of the bounces (in the order from the most recent to the oldest)
# * bounce pips. Length from the horizontal line defined by IC until the highest point of the bounce (considering wicks also)
# * inn_bounce. Number of candles of the inner bounce (see screenshots below)
# indecission	Number of candles the price stays in S/R, without considering the bounce and only considering the candles pre/post bounce
# * retraced.	Only relevant for outcome=F, how many pips from the S/L the trade reversed?. If n.a., then it means that the trade did not reversed last time that the price was below/above this level assuming that a possible counter could happen
# * entry_aligned. Is the entry aligned with previous bounces on the same trend. TRUE or 1 if it is, FALSE or 0 if it is not
# * trend_bounces. Discrete quantitative variable representing the number of bounces at the trend

# ## Dependencies

# In[260]:


import pandas as pd
import numpy as np
import pdb
import re
import math
import seaborn as sns
from pandas.plotting import scatter_matrix
from sklearn.metrics import confusion_matrix,precision_score
from sklearn.model_selection import train_test_split

get_ipython().run_line_magic('matplotlib', 'inline')


# # Continuation trades
# 
# First, let's create a function to read-in a .csv file containing the data andstore it in a dataframe:

# In[261]:


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

contDF=read_tradedata('/Users/ernesto/Downloads/Screenshot analysis - train_continuations.tsv',sep="\t",na_values=["n.a.","n.a"])

contDF.shape


# And some information about contDF:

# In[262]:


contDF.info()


# * Conversion to right types<br>
# Let's convert now the `start` and `last time` variables to DateTime

# In[263]:


contDF['start']= pd.to_datetime(contDF['start'])
contDF['last time']= pd.to_datetime(contDF['last time'])


# ## Cleaning the n.a. values
# The following predictors have n.a. values and the strategy I will follow will depend on each case:

# * No of candles (will replace the n.a. by 0)

# In[264]:


if "No of candles" in contDF: contDF["No of candles"].fillna(0, inplace=True)


# * Bounce length (will replace the n.a. by 0)

# In[265]:


contDF["bounce length"].fillna(0, inplace=True)


# * Length of trend (-1) (will replace the n.a. by 0)

# In[266]:


contDF["length of trend (-1)"].fillna(0, inplace=True)


# * Length in pips (-1) (will replace the n.a. by 0)

# In[267]:


contDF["length in pips (-1)"].fillna(0, inplace=True)


# ## Normalize
# Let's normalize all variables dealing with pips.

# In[268]:


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
    
    


# In[269]:


contDF['norm_length_pips']=contDF.apply(normalize,axis=1, variable_name='length in pips (-1)')
contDF['norm_bounce_pips']=contDF.apply(normalize,axis=1, variable_name='bounce (pips)')
contDF['norm_retraced']=contDF.apply(normalize,axis=1, variable_name='retraced')


# ## Transforming

# In[270]:


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

if "ext_outcome" in contDF: contDF['ext_outcome']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='ext_outcome')
contDF['outcome']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='outcome')
contDF['entry on RSI']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='entry on RSI')
if "strong_trend" in contDF: contDF['strong trend']=contDF.apply(digit_binary,axis=1,transl_dict=transl_dict, name='strong trend')


# ## Selecting the desired timeframe

# contDF=contDF[contDF.timeframe == 'H6']

# ## Checking the redudant trades
# Let's sort the trades by date to check if there are reduntant trades:
sortedDF=contDF.sort_values(by='start')
print(sortedDF)

sortedDF.to_csv('/Users/ernesto/Downloads/sorted_contDF.tsv',sep='\t')
# ## Calculating extended outcome based on the norm_retraced variable
# Trades having retraced by less that a cut off number of pips will be considered Successful

# In[271]:


def calc_extoutcome(row,cutoff=20):
    if not math.isnan(row['norm_retraced']):
        if row['norm_retraced']<=cutoff:
            return int(1)
        else:
            return int(0)
    else:
        return int(row['outcome'])
        
            


# In[272]:


contDF['ext_outcome']=contDF.apply(calc_extoutcome,axis=1)


# ## Selecting the trades having entry_aligned=1
contDF=contDF.loc[contDF['entry_aligned']==1]
# ## Initial exploration of the data
# 
# First things first, let's examine if we have a significant number of records per category of the dependent variable (outcome in this case), since it is really very important to have enough records to establish solid conclusions

# outcome_ix=5
# outcome_lab="outcome"
# contDF.iloc[:,outcome_ix].value_counts()

# In[273]:


outcome_ix=34
outcome_lab="ext_outcome"
contDF.iloc[:,outcome_ix].value_counts()


# ### Inn_bounce/Indecisison ratio
# Float variable representing the ratio between the internal bounce divided by the indecission ratio

# In[2073]:


contDF['bounce_ratio']=contDF['inn_bounce']/contDF['indecission']


# In[2074]:


ax = sns.boxplot(x=outcome_lab, y="bounce_ratio", data=contDF)


# * Mean for each category

# In[2075]:


contDF.groupby(outcome_lab).agg({'bounce_ratio': 'mean'})


# * Median for each category

# In[2076]:


contDF.groupby(outcome_lab).agg({'bounce_ratio': 'median'})


# Let's analyze the distribution with a histogram

# In[2077]:


succ=contDF.loc[contDF[outcome_lab]==1]['bounce_ratio']
fail=contDF.loc[contDF[outcome_lab]==0]['bounce_ratio']


# In[2078]:


plt.hist([fail,succ], bins = 15, normed=True, label=['0','1'])

plt.legend()
plt.xlabel('Bounce ratio')
plt.ylabel('Normalized Freq')
plt.title('Hist for Bounce ratio on the outcome')


# In[2079]:


plt.xlim(0,20)
plt.hist([fail,succ], bins = 15, normed=True, label=['0','1'])

plt.legend()
plt.xlabel('Bounce ratio')
plt.ylabel('Normalized Freq')
plt.title('Hist for Bounce ratio depending on the outcome')


# ## Calculating points
# This section will calculate a total score for each trade that will be used to predict the outcome.<br>

# First, let's create a function to calculate the points

# In[2080]:


def calculate_points(row,attribs):
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
               
    Returns
    -------
    Returns a score for this trade
    
    '''
    score=0
    for a in attribs:
        value=row[a['attr']]
        cutoffs=a['cutoffs']
        points=a['points']
        if cutoffs =='bool':
            if a['rel'] == 'is_true':
                if value == True or value == 1:
                    score+=points
                if value == False  or value == 0:
                    score+=-1*points
        else:
            if len(cutoffs)!= len(points):
                raise Exception("Length of cutoffs is different to length of points")
            for i, j in zip(cutoffs, points):
                if value>=i[0] and value<=i[1]:
                    score+=j
                
    return score


# # ALL
# attbs=[]
# 
# attbs.append({
#         'attr' : 'RSI bounces',
#         'cutoffs' : [(0,2), (3,3), (4,100000)],
#         'points' : [2,-1,-2]
#         })
# attbs.append({
#         'attr' : 'entry on RSI',
#         'cutoffs' : 'bool',
#         'rel' : 'is_true',
#         'points' : 3
#         })
# attbs.append({
#         'attr' : 'length of trend (-1)',
#         'cutoffs' : [(0,50),(51,60),(61,10000)],
#         'points' : [2,1,-2]
#         })
# attbs.append( {
#         'attr' : 'inn_bounce',
#         'cutoffs' : [(0,7),(8,1000000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'pips_ratio_norm',
#         'cutoffs' : [(0,3),(4,30)],
#         'points' : [-2,2]
#         })
# attbs.append( {
#         'attr' : 'sum_bounces',
#         'cutoffs' : [(0,7),(8,100000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'norm_bounce_pips',
#         'cutoffs' : [(0,48),(49,1000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'entry_aligned',
#         'cutoffs' : 'bool',
#         'rel' : 'is_true',
#         'points' : 6
#         })
# attbs.append( {
#         'attr' : 'indecission',
#         'cutoffs' : [(0,3),(4,5),(6,100)],
#         'points' : [1,-1,-2]
#         })
# attbs.append( {
#         'attr' : 'bounce_ratio',
#         'cutoffs' : [(0,3),(4,10000)],
#         'points' : [-2,2]
#         })

# In[2081]:


# ALL and entry_aligned=1
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


# # D
# attbs=[]
# 
# attbs.append({
#         'attr' : 'diff',
#         'cutoffs' : [(0,300),(301,100000)],
#         'points' : [2,-2]
#         })
# attbs.append({
#         'attr' : 'RSI bounces',
#         'cutoffs' : [(0,2), (3,3), (4,100000)],
#         'points' : [2,-1,-2]
#         })
# attbs.append({
#         'attr' : 'entry on RSI',
#         'cutoffs' : 'bool',
#         'rel' : 'is_true',
#         'points' : 3
#         })
# attbs.append( {
#         'attr' : 'length of trend (-1)',
#         'cutoffs' : [(0,10),(11,14),(15,23),(24,50),(51,10000)],
#         'points' : [-1,1,2,1,-2]
#         })
# attbs.append( {
#         'attr' : 'inn_bounce',
#         'cutoffs' : [(0,7),(8,1000000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'pips_ratio',
#         'cutoffs' : [(0,150),(151,220),(221,1000000000000)],
#         'points' : [-2,1,2]
#         })
# attbs.append( {
#         'attr' : 'sum_bounces',
#         'cutoffs' : [(0,6),(7,1000000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'bounce (pips)',
#         'cutoffs' : [(0,800),(801,1000000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'entry_aligned',
#         'cutoffs' : 'bool',
#         'rel' : 'is_true',
#         'points' : 6
#         })
# attbs.append( {
#         'attr' : 'indecission',
#         'cutoffs' : [(0,3),(4,20)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'bounce_ratio',
#         'cutoffs' : [(0,4),(5,10000)],
#         'points' : [-2,2]
#         })

# # H12
# attbs=[]
# 
# attbs.append({
#         'attr' : 'diff',
#         'cutoffs' : [(0,600),(601,100000)],
#         'points' : [2,-2]
#         })
# attbs.append({
#         'attr' : 'RSI bounces',
#         'cutoffs' : [(0,1),(2,2),(3,6),(7,100000)],
#         'points' : [2,1,-1,-2]
#         })
# attbs.append({
#         'attr' : 'entry on RSI',
#         'cutoffs' : 'bool',
#         'rel' : 'is_true',
#         'points' : 3
#         })
# attbs.append( {
#         'attr' : 'length of trend (-1)',
#         'cutoffs' : [(0,9), (10,99),(100,1000000)],
#         'points' : [-1,1,-1]
#         })
# attbs.append( {
#         'attr' : 'inn_bounce',
#         'cutoffs' : [(0,7),(8,1000000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'pips_ratio',
#         'cutoffs' : [(0,150),(151,1000000000000)],
#         'points' : [-2,2]
#         })
# attbs.append( {
#         'attr' : 'sum_bounces',
#         'cutoffs' : [(0,4),(5,100000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'bounce (pips)',
#         'cutoffs' : [(0,900),(901,1000000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'entry_aligned',
#         'cutoffs' : 'bool',
#         'rel' : 'is_true',
#         'points' : 6
#         })
# attbs.append( {
#         'attr' : 'indecission',
#         'cutoffs' : [(0,5),(6,20)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'bounce_ratio',
#         'cutoffs' : [(0,6),(7,10000)],
#         'points' : [2,-2]
#         })

# #H6
# attbs=[]
# 
# attbs.append({
#         'attr' : 'diff',
#         'cutoffs' : [(0,350),(351,1000000)],
#         'points' : [-2,2]
#         })
# attbs.append({
#         'attr' : 'RSI bounces',
#         'cutoffs' : [(0,0),(1,3),(4,1000)],
#         'points' : [-1,2,-1]
#         })
# attbs.append({
#         'attr' : 'entry on RSI',
#         'cutoffs' : 'bool',
#         'rel' : 'is_true',
#         'points' : 3
#         })
# attbs.append( {
#         'attr' : 'inn_bounce',
#         'cutoffs' : [(0,5),(6,1000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'pips_ratio',
#         'cutoffs' : [(0,100),(101,10000)],
#         'points' : [-1,1]
#         })
# attbs.append( {
#         'attr' : 'sum_bounces',
#         'cutoffs' : [(0,3),(4,100000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'bounce (pips)',
#         'cutoffs' : [(0,600),(601,1000000)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'entry_aligned',
#         'cutoffs' : 'bool',
#         'rel' : 'is_true',
#         'points' : 6
#         })
# attbs.append( {
#         'attr' : 'indecission',
#         'cutoffs' : [(0,1),(2,10)],
#         'points' : [2,-2]
#         })
# attbs.append( {
#         'attr' : 'bounce_ratio',
#         'cutoffs' : [(0,5),(6,1000)],
#         'points' : [-2,2]
#         })

# Now, let's apply the calculate_points on each row of the dataframe

# In[2082]:


contDF['score']=contDF.apply(calculate_points, axis=1, attribs=attbs)


# Examining trades with score above the chosen cutoff but failing:

# In[2083]:


print(outcome_lab)
contDF.loc[(contDF[outcome_lab]==0) & (contDF['score']>3)]


# ### Calculating cutoff score
# * Mean

# In[2084]:


contDF.groupby(outcome_lab).agg({'score': 'mean'})


# * Median

# In[2085]:


contDF.groupby(outcome_lab).agg({'score': 'median'})


# * Histogram

# In[2086]:


axList=contDF['score'].hist(by=contDF[outcome_lab],figsize=(20,5),bins=8,normed=True)


# In[2087]:


succ=contDF.loc[contDF[outcome_lab]==1]['score']
fail=contDF.loc[contDF[outcome_lab]==0]['score']


# In[2088]:


plt.hist([fail,succ], bins = 15, normed=True, label=['0','1'])

plt.legend()
plt.xlabel('Score')
plt.ylabel('Normalized Freq')
plt.title('Outcome of trade depending on score')


# ### Making predictions and performance evaluation
# We will use different cutoffs and make predictions using these using the test set

# Let's create a new dataframe only with the columns we are interested in:

# In[2089]:


scoreDF=contDF.iloc[:,[outcome_ix,37]]


# In[2090]:


def predictOutcome(row, cutoff):
    pred=None
    if row['score'] >cutoff:
        pred=1
    else:
        pred=0
    return pred


# In[2091]:


scoreDF['predict']=scoreDF.apply(predictOutcome,axis=1,cutoff=10)


# * Performance evaluation

# In[2092]:


(tn, fp, fn, tp)=confusion_matrix(scoreDF[outcome_lab], scoreDF['predict']).ravel()
print("TP:"+str(tp))
print("TN:"+str(tn))
print("FN:"+str(fn))
print("FP:"+str(fp))


#     * Precision

# In[2093]:


print(tp/(tp+fp))


# * Recall

# In[2094]:


print(tp/(tp+fn))


# ### Cross-validation

# In[2095]:


def cross_validate(cutoff,iterations):
    '''
    Function that will asses the sensitivity and specificity for differnt cutoff scores
    on different slices of the input dataframe
    
    Parameters
    ----------
    cutoff: int
            Cut off value used for predicting a trade as S or F
    iterations: int
                 Number of crossvalidation iterations
    '''
    precision_list=[]
    recall_list=[]
    tp_list=[]
    precission_list,recall_list,tn_list,fp_list,fn_list,tp_list = ([] for i in range(6))
    
    for i in range(0,iterations,1):
        #print("[WARN]: Iteration {0}".format(i))
        train, test = train_test_split(contDF,
                                       test_size=0.99)
        test['score']=test.apply(calculate_points, axis=1, attribs=attbs)
    
        scoreDF=test.iloc[:,[outcome_ix,37]]
        scoreDF['predict']=scoreDF.apply(predictOutcome,axis=1,cutoff=cutoff)
        # assess performance
        (tn, fp, fn, tp)=confusion_matrix(scoreDF[outcome_lab], scoreDF['predict']).ravel()
        precision_list.append(tp/(tp+fp))
        recall_list.append(tp/(tp+fn))
        tn_list.append(tn)
        fp_list.append(fp)
        fn_list.append(fn)
        tp_list.append(tp)
    precission_array=np.array([precision_list])
    recall_array=np.array([recall_list])
    tn_array=np.array([tn_list])
    fp_array=np.array([fp_list])
    fn_array=np.array([fn_list])
    tp_array=np.array([tp_list])
    print("Precission: AGV: {0},STD:{1},CUTOFF:{2}".format(np.average(precission_array),np.std(precission_array),cutoff))
    print("Recall: AGV: {0},STD:{1},CUTOFF:{2}".format(np.average(recall_array),np.std(recall_array),cutoff))
    print("TN: AGV: {0},STD:{1},CUTOFF:{2}".format(np.average(tn_array),np.std(tn_array),cutoff))
    print("FP: AGV: {0},STD:{1},CUTOFF:{2}".format(np.average(fp_array),np.std(fp_array),cutoff))
    print("FN: AGV: {0},STD:{1},CUTOFF:{2}".format(np.average(fn_array),np.std(fn_array),cutoff))
    print("TP: AGV: {0},STD:{1},CUTOFF:{2}".format(np.average(tp_array),np.std(tp_array),cutoff))


# Now, let's iterate a number of times (1000 in this case) on different cutoffs

# In[2096]:


for i in range(-10,20,1):
    cross_validate(i,1)


# ### Using a Binary classifier
# First, let's prepare the data by separating the data into labels (dependent variable, which is the variable we try to predict) and features (the independent variables that are going to be used for the model)

# In[ ]:


labels=contDF['ext_outcome']
features=contDF.drop(["ext_outcome","outcome"],axis=1)


# We need also to remove some features that will be not accepted by the classifier or are not useful

# In[ ]:


features=features.drop(["id","start","timeframe","entry","retraced","last time","target","bounce length","space interswings"],axis=1)


# Now, let's split our data into training and test sets. In this case, the test_size=0.33

# In[ ]:


train, test, train_labels, test_labels = train_test_split(features,
                                                          labels,
                                                          test_size=0.33,
                                                          random_state=42)


# As the counts for each outcome category are unbalanced, I will oversample using SMOTE:

# In[ ]:


from imblearn.over_sampling import SMOTE

train_resampled, trainlabels_resampled = SMOTE().fit_sample(train,train_labels)


# Let's check the balanced counts:

# In[ ]:


from collections import Counter

print(sorted(Counter(trainlabels_resampled).items()))


# #### naive_bayes

# Building and Evaluating the Model for the non oversampled train dataset

# In[ ]:


from sklearn.naive_bayes import GaussianNB

# Initialize our classifier
gnb = GaussianNB()

# Train our classifier
model = gnb.fit(train, train_labels)


# In[ ]:


# Make predictions
preds = gnb.predict(test)


# In[ ]:


from sklearn.metrics import accuracy_score

# Evaluate accuracy
print(accuracy_score(test_labels, preds))


# Now, with the oversampled train dataset

# In[ ]:


# Train our classifier
model = gnb.fit(train_resampled,  trainlabels_resampled)

# Make predictions
preds = gnb.predict(test)

# Evaluate accuracy
print(accuracy_score(test_labels, preds))


# **Conclusion** It is slightly better using oversampling

# #### Using SGDClassifier
# First, let's use the non oversampled train dataset

# In[ ]:


from sklearn.linear_model import SGDClassifier

sgd_clf = SGDClassifier()
sgd=sgd_clf.fit(train,train_labels)


# In[ ]:


preds=sgd_clf.predict(test)


# In[ ]:


print(accuracy_score(test_labels, preds))


# Now, with the oversampled train dataset

# In[ ]:


sgd_clf = SGDClassifier()
sgd=sgd_clf.fit(train_resampled,trainlabels_resampled)
preds=sgd_clf.predict(test)
print(accuracy_score(test_labels, preds))


# #### Using Logistic Regression  
# First, let's use the non oversampled train dataset

# In[ ]:


from sklearn.linear_model import LogisticRegression
logisticRegr = LogisticRegression(verbose=1)


# Now, we train the model with the training set:

# In[ ]:


m=logisticRegr.fit(train, train_labels)


# Now, let's measue model performance
# First, we are going to make predictions using our new model and the test data

# In[ ]:


predictions = logisticRegr.predict(test)


# We can use the score function in order to calculate the mean accuracy on the test data and labels

# In[ ]:


score = logisticRegr.score(test, test_labels)
print(score)


# In order to visualize the correctness of our predictions, we can also create a confusion matrix:

# In[ ]:


import matplotlib.pyplot as plt
import seaborn as sns
from sklearn import metrics

cm = metrics.confusion_matrix(test_labels, predictions)
print(cm)


# The matrix above can be embellished by using seaborn:

# In[ ]:


plt.figure(figsize=(9,9))
sns.heatmap(cm, annot=True, fmt=".0f", linewidths=.5, square = True, cmap = 'Blues_r');
plt.ylabel('Actual label');
plt.xlabel('Predicted label');
all_sample_title = 'Accuracy Score: {0}'.format(score)
plt.title(all_sample_title, size = 15);


# Now, let's try with the oversampled train dataset

# In[ ]:


from sklearn.linear_model import LogisticRegression
logisticRegr = LogisticRegression(verbose=1)


# Now, we train the model with the training set:

# In[ ]:


m=logisticRegr.fit(train_resampled,trainlabels_resampled)


# Now, let's measue model performance
# First, we are going to make predictions using our new model and the test data

# In[119]:


predictions = logisticRegr.predict(test)


# We can use the score function in order to calculate the mean accuracy on the test data and labels

# In[120]:


score = logisticRegr.score(test, test_labels)
print(score)


# **Conclusion:** It is worst to oversample in terms of score

# * Examining the influence of each predictor on the outcome

# In[121]:


stds=np.std(train, 0)

print(stds.values*m.coef_)


# In[ ]:


keys=list(train.columns)
values_10=list(stds.values*m.coef_)[0]*10

coefficients=dict(zip(keys,values_10))
print(coefficients)


# **Conclusions:**  
# * Relevant  
# {{train.columns[0]}} (negative)  
# {{train.columns[1]}} (negative)  
# {{train.columns[2]}} (positive)  
# {{train.columns[4]}} (negative)  
# {{train.columns[5]}} (positive)  
# {{train.columns[7]}} (positive)  
# {{train.columns[8]}} (negative)  
# {{train.columns[9]}} (negative)  
# {{train.columns[10]}} (positive)  
# {{train.columns[11]}} (negative)  
# {{train.columns[12]}} (positive)  
# {{train.columns[13]}} (negative)  
# {{train.columns[14]}} (positive)  

# * Irrelevant  
# {{train.columns[3]}}  
# {{train.columns[6]}}  
# {{train.columns[15]}}
