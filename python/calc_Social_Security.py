import os
import pandas as pd
import numpy as np

def calc_social_security_benefit(avg_salary, claim_age):
    #dfSS = pd.read_csv('../data/SS.csv')
    dfSS = pd.read_csv('data/SS.csv')
    index_value = claim_age - 62
    avg_monthly_salary = avg_salary / 12
    first_bend_point = 926
    second_bend_point = 5583
    max_monthly_benefit = 3000 #what is 2019 value?
    PIA_monthly = (min((min(avg_monthly_salary, first_bend_point) * 0.9
                   + min(max(avg_monthly_salary - first_bend_point,0), second_bend_point - first_bend_point) * 0.32
                   + max(avg_monthly_salary - second_bend_point,0) * 0.15), max_monthly_benefit))

    SS_benefit_ratio = dfSS.Ratio[index_value]
    SS_pre_tax_ben = SS_benefit_ratio * PIA_monthly * 12

    return SS_pre_tax_ben
