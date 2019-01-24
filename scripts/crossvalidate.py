import pandas as pd
import argparse

parser = argparse.ArgumentParser(description='Script to crossvalidate and assess the Precission and Recall values of different slices of the data')

parser.add_argument('--DF', required=True, help='input dataframe')
args = parser.parse_args()

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

def cross_validate(cutoff,iterations):
    '''
    Function that will asses the precission and recall values for differnt cutoff scores
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
                                       test_size=0.25)
        train['score']=train.apply(calculate_points, axis=1, attribs=attbs)
        test['score']=test.apply(calculate_points, axis=1, attribs=attbs)
    
        scoreDF=test.iloc[:,[outcome_ix,34]]
        scoreDF['predict']=scoreDF.apply(predictOutcome,axis=1,cutoff=cutoff)
        # assess performance
        (tn, fp, fn, tp)=confusion_matrix(scoreDF['outcome'], scoreDF['predict']).ravel()
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

#read in the dataframe with the trades
contDF=pd.read_csv(args.DF,sep="\t",na_values=["n.a.","n.a"])

#convert start and last_time to datetime
contDF['start']= pd.to_datetime(contDF['start'])
contDF['last time']= pd.to_datetime(contDF['last time'])

#replace n.a. values by 0
contDF["bounce length"].fillna(0, inplace=True)
contDF["length of trend (-1)"].fillna(0, inplace=True)
contDF["length in pips (-1)"].fillna(0, inplace=True)

#normalize the variables dealing with pips
contDF['norm_length_pips']=contDF.apply(normalize,axis=1, variable_name='length in pips (-1)')
contDF['norm_bounce_pips']=contDF.apply(normalize,axis=1, variable_name='bounce (pips)')
