# -*- coding: utf-8 -*-
"""Created on Sat Jan 26 00:55 2019
@author: Paul J Kowalczyk
octanol-water partition coefficient ... LogHL
"""

### Instantiate environment
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.ML.Descriptors import MoleculeDescriptors
from rdkit.Chem import PandasTools
import pandas as pd
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt 
import numpy as np
import math
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import datetime

### Read data
train_df = PandasTools.LoadSDF("data/TR_HL_441.sdf")
test_df = PandasTools.LoadSDF("data/TST_HL_150.sdf")

### Concatenate data
LogHL = pd.concat([train_df[["Canonical_QSARr", "LogHL"]],
                 test_df[["Canonical_QSARr", "LogHL"]]], ignore_index = True)
LogHL['LogHL'] = pd.to_numeric(LogHL['LogHL'])

### Calculate features
nms = [x[0] for x in Descriptors._descList]
calc = MoleculeDescriptors.MolecularDescriptorCalculator(nms)
for i in range(len(LogHL)):
    try:
        descrs = calc.CalcDescriptors(Chem.MolFromSmiles(LogHL.iloc[i, 0]))
        for x in range(len(descrs)):
            LogHL.at[i, str(nms[x])] = descrs[x]
    except:
        for x in range(len(descrs)):
            LogHL.at[i, str(nms[x])] = 'NaN'    
            
LogHL = LogHL.dropna()

### Training & Test Datasets
X = LogHL.drop(columns=["Canonical_QSARr", "LogHL"])
y = LogHL[["LogHL"]]
X_train, X_test, y_train, y_test = train_test_split(X, y,
                                                    random_state = 350,
                                                    test_size = 0.2)

### Identify / remove near-zero variance descriptors
def variance_threshold_selector(data, threshold = 0.5):
    selector = VarianceThreshold(threshold)
    selector.fit(data)
    return data[data.columns[selector.get_support(indices = True)]]

nzv = variance_threshold_selector(X_train, 0.0)

X_train = X_train[nzv.columns]
X_test = X_test[nzv.columns]

### Identify / remove highly correlated descriptors
corr_matrix = X_train.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape),
                                  k = 1).astype(np.bool))
to_drop = [column for column in upper.columns
           if any(upper[column] > 0.85)]

X_train = X_train[X_train.columns.drop(to_drop)]
X_test = X_test[X_test.columns.drop(to_drop)]

### standardize features by removing the mean and scaling to unit variance
scaler = StandardScaler()
scaler.fit(X_train)

X_train_standard = scaler.transform(X_train)
X_test_standard = scaler.transform(X_test)

#####
##### TPOT
#####

print(datetime.datetime.now())
from tpot import TPOTRegressor
tpot = TPOTRegressor(generations=10, population_size=50, verbosity=2)
tpot.fit(X_train_standard, y_train)
print(tpot.score(X_test_standard, y_test))
tpot.export('tpot_LogHL_pipeline.py')
print(datetime.datetime.now())

