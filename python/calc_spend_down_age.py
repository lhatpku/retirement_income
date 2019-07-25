import os
import pandas as pd
import numpy as np

def calc_spend_down_age(age, gender, confidence_level):

    mortality_table = pd.read_csv('data/mortality.csv', header=0, sep=',', index_col=0)

    #Calculate Survival Probability
    SurvivalProbability = []
    tPx = 1
    percentile = 1 - confidence_level

    if gender == 'Male':

        for x in range(120 - age):
            tPx = tPx * (1 - mortality_table.Male[x + age])
            SurvivalProbability.append(tPx)

    elif gender == 'Female':

        for x in range(120 - age):
            tPx = tPx * (1 - mortality_table.Female[x + age])
            SurvivalProbability.append(tPx)

    PlanningHorizon = 1 + sum(1 for px in SurvivalProbability if px > percentile)

    return PlanningHorizon + age
    
