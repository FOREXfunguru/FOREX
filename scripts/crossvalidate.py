import pandas as pd
import argparse
import os
import numpy as np

from sklearn.metrics import confusion_matrix,precision_score

parser = argparse.ArgumentParser(description='Script to crossvalidate and assess the Precission and Recall values of different slices of the data')

parser.add_argument('--ifile', required=True, help='input dataframe with scores in it')
parser.add_argument('--timeframe', required=True, help='Input dataframe. Valid values are: ALL,D,H12,H6')
parser.add_argument('--outcome', required=True, help='outcome type. Possible values are outcome or ext_outcome')
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

if args.timeframe != 'ALL':
    DF=DF[DF['timeframe']==args.timeframe]

print("Total # of records for desired timeframe: {0}; # of variables: {1}".format(DF.shape[0], DF.shape[1]))

def predictOutcome(row, cutoff):
    pred=None
    if row['score'] >cutoff:
        pred=1
    else:
        pred=0
    return pred

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
        DF['predict']=DF.apply(predictOutcome,axis=1,cutoff=cutoff)
        # assess performance
        (tn, fp, fn, tp)=confusion_matrix(DF[args.outcome], DF['predict']).ravel()
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

for i in range(0,6,1):
    cross_validate(i,1)
