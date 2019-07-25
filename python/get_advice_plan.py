import os
import pandas as pd
import numpy as np

def get_advice_plan(profile,goal,config,forecast):
    return {'advice_1':f'Advice_1: Age is {profile["age"]} and Gender is {profile["gender"]}','advice_2':f'Advice_2: Age is {profile["age"]+30} and Name is {profile["name"]}',\
    'advice_3':f'Advice_3: Age is {profile["age"]+50} and Name is {profile["name"]}'}



#Calculate Retirement Starting Year (relative to projection start) with years-to-retirement-view
#Future Goal SubProcess - difference between target and all guaranteed income over time


# for each calendar year in the projection, determine the total modified duration over the projection starting in that calendar year
## modified duration is based on the standard modified duration calculation sum of (n * PV of CF) across n / sum of PV of CFs across n
## 
