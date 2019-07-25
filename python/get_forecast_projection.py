import os
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP
from calc_tax import calc_income_tax_liability, calc_fica_tax_liability, calc_take_home_income
import json
from scipy.optimize import minimize

test = True

if test == True:

    fica_loc = os.path.join('../data','fica_tax.json')
    income_tax_loc = os.path.join('../data','income_tax.json')
    fica_config = json.loads(open(fica_loc).read())
    income_tax_config = json.loads(open(income_tax_loc).read())

#Assumptions
num_model_ports = 100
num_sim_runs = 100
num_sim_years = 100

def load_glide_path():
    if test == True:
        dfGlidePath = pd.read_csv('../data/Glidepath.csv')
    else:
        dfGlidePath = pd.read_csv('data/Glidepath.csv')
    #print(dfGlidePath.EquityLevel[5])
    return dfGlidePath

dfGlidePath = load_glide_path()

def load_model_portfolios():
    if test == True:
        dfModelPorts = pd.read_csv('../data/modelPortfolio.csv', header = None)
    else:
        dfModelPorts = pd.read_csv('data/modelPortfolio.csv', header = None)
    #print(dfModelPorts.iat[0,0])
    return dfModelPorts

dfModelPorts = load_model_portfolios()

def determine_glide_path(spend_down_age, age):
    planning_horizon = spend_down_age - age
    equity_allocation_over_time = np.zeros((planning_horizon))
    for n in range(planning_horizon):
        equity_allocation_over_time[n] = dfGlidePath.EquityLevel[age + n]
    return equity_allocation_over_time

def lookup_closest_model_port(equity_allocation_over_time, projection_year):
    temp = round(equity_allocation_over_time[projection_year] * 100 / 0.01) * 0.01
    model_port = Decimal(temp).to_integral_value(rounding = ROUND_HALF_UP)
    return model_port

def load_sim_runs():
    #Create dictionary of data frames for each asset class simulation return file
    if test == True:
        root = '../data/Simulation_Returns'
    else:
        root = 'data/Simulation_Returns'
    ddict = {}
    asset_class_names = []
    for file in os.listdir(root):
        name = os.path.splitext(file)[0]
        asset_class_names.append(name)
        ddict[name] = pd.read_csv(os.path.join(root, file),header = None)
    #print(ddict['Emerging Markets Bond'].iat[1,0])
    return ddict, asset_class_names

DFs_asset_class_sim_run, asset_class_sim_run_ordering = load_sim_runs()

#ordering in dfModelPorts
mp_asset_class_column_ordering = ['Commodities','Global ex-US REIT','US REIT','Emerging Markets Equity','Developed Markets Large Cap',
                              'US Small Cap Growth','US Small Cap Value','US Large Cap Growth','US Large Cap Value',
                              'Global ex-US Small Cap','Emerging Markets Bond','Developed Markets Bond','US High Yield Bond',
                              'US Treasury Bond - 5 Plus Years','US Treasury Bond - 1 to 5 Years','US Corporate Bond',
                              'US Agency Bond','US Mortgage Backed Bond','US Municipal Bond','TIPS','Short-Term']

def calc_model_port_ret_across_sim_runs_at_projection_year(model_port, projection_year, mp_asset_class_column_ordering, dfModelPorts, DFs_asset_class_sim_run):
    asset_class_sim_run_matrix = np.zeros((len(mp_asset_class_column_ordering), 100))
    projection_year = projection_year

    #Determine asset class sim run 21 x 100 matrix
    for i, name in enumerate(mp_asset_class_column_ordering):
        asset_class_sim_run_matrix[i][:] = DFs_asset_class_sim_run[name].iloc[:,projection_year]

    #Determine model_portfolio asset allocation weights 1 x 21 matrix
    model_port_asset_class_matrix = dfModelPorts.iloc[[model_port]]

    #Calculate model portfolio simulated output across all sim runs for specified projection year
    model_port_sim_run_output = np.matmul(model_port_asset_class_matrix, asset_class_sim_run_matrix)
    
    # if test == True:
    #     pd.DataFrame(model_port_sim_run_output).to_csv('../data/test_model_portfolio_output.csv')
    return model_port_sim_run_output

def convert_contributions(raw_ctrbs, tax_types, salary):
    ctrbs = np.zeros(len(tax_types))
    for x in range(0, len(tax_types)):
        if raw_ctrbs[x] < 1:
            ctrbs[x] = raw_ctrbs[x] * salary
        else:
            ctrbs[x] = raw_ctrbs[x]
    return ctrbs

def accumulate(age, ret_age, ctrbs, starting_wealth, model_port, projection_year, tax_types, num_sim_runs):
    ModelPortReturnsBySimAndYear = calc_model_port_ret_across_sim_runs_at_projection_year(model_port, projection_year,
                                                                                        mp_asset_class_column_ordering, dfModelPorts, DFs_asset_class_sim_run)

    EOY_wealth = np.zeros((num_sim_runs,len(tax_types)))

    for i in range(num_sim_runs):
        for x in range(len(tax_types)):
            EOY_wealth[i][x] = starting_wealth[x] * (1 + ModelPortReturnsBySimAndYear[:,i]) + ctrbs

    return EOY_wealth

def initalize_arrays_that_vary_over_time(age, spend_down_age, tax_types, starting_wealth):

    planning_horizon = spend_down_age - age

    #Initalize glide path
    equity_allocation_over_time = determine_glide_path(spend_down_age,age)

    #define arrays of values that will vary over time
    beg_wealth_over_time = np.zeros((planning_horizon, num_sim_runs, len(tax_types)))
    end_wealth_over_time = np.zeros((planning_horizon,num_sim_runs, len(tax_types)))

    #Set initial wealth at time 0
    for i in range(100):
        beg_wealth_over_time[0][i][:] = initial_wealth

    return equity_allocation_over_time, beg_wealth_over_time, end_wealth_over_time

#Objective Function and constraints
def ObjectiveFunction(pre_tax_withdrawal):
    return calc_take_home_income(gross_income = pre_tax_withdrawal,pre_tax_contrib = 0,post_tax_contrib = 0,income_tax_config = income_tax_config,fica_config = fica_config)
#Constraint
def const_function(pre_tax_withdrawal):
    return (calc_take_home_income(gross_income = pre_tax_withdrawal,pre_tax_contrib = 0,post_tax_contrib = 0,
            income_tax_config = income_tax_config,fica_config = fica_config) - post_tax_withdrawal)

#const = {'type': 'ineq', 'fun':const_function}

def decumulate(age, ret_age, post_tax_withdrawal, starting_wealth, model_port, projection_year, tax_types, num_sim_runs, after_tax_social_security):
    ModelPortReturnsBySimAndYear = calc_model_port_ret_across_sim_runs_at_projection_year(model_port, projection_year,
                                                                                        mp_asset_class_column_ordering, dfModelPorts, DFs_asset_class_sim_run)
    EOY_wealth = np.zeros((num_sim_runs,len(tax_types)))
    withdrawal = np.zeros((num_sim_runs,len(tax_types)))
    after_tax_retirement_income = np.zeros((num_sim_runs,len(tax_types)))

    # Define the optimization function 
    def const_function(pre_tax_withdrawal):
        income_tax_liability = calc_income_tax_liability(pre_tax_withdrawal, after_tax_social_security, income_tax_config)
        return abs(pre_tax_withdrawal + after_tax_social_security - income_tax_liability - post_tax_withdrawal)
    
    const = {'type': 'ineq', 'fun':const_function}
    solution = minimize(fun=ObjectiveFunction, x0 = post_tax_withdrawal/0.7, constraints = const)
    optimized_pre_tax_withdrawal = solution.x

    for i in range(num_sim_runs):
        for x in range(len(tax_types)):
            EOY_wealth[i][x] = max(starting_wealth[x] * (1 + ModelPortReturnsBySimAndYear[:,i]) - optimized_pre_tax_withdrawal, 0)
            if starting_wealth[x] * (1 + ModelPortReturnsBySimAndYear[:,i]) - optimized_pre_tax_withdrawal >= 0: #withdrawal is fully funded
                withdrawal[i][x] = optimized_pre_tax_withdrawal
            else: #not fully funded
                withdrawal[i][x] = max(0, starting_wealth[x] * (1 + ModelPortReturnsBySimAndYear[:,i]))

            after_tax_retirement_income[i][x] = calculate_after_tax_retirement_income(after_tax_social_security, withdrawal[i][x])

    return EOY_wealth, after_tax_retirement_income

def ruin_probability(income_over_time, post_tax_withdrawal,target_income):
    ruin_probability = sum (1 for income in income_over_time if income < target_income)
    return ruin_probability

def calc_after_tax_social_security_benefit(pre_tax_social_security_benefit):
    after_tax_social_security = pre_tax_social_security_benefit  * 0.85
    return after_tax_social_security

def calculate_after_tax_retirement_income(after_tax_social_security, withdrawal):

    after_tax_retirement_income = calc_take_home_income(gross_income = withdrawal, pre_tax_contrib = 0,post_tax_contrib = 0,
                                                        income_tax_config = income_tax_config,fica_config = fica_config) + after_tax_social_security
    return after_tax_retirement_income

def determine_post_tax_withdrawal(social_security_ben, target_income, annuity_inc = 0):
    after_tax_social_security = calc_after_tax_social_security_benefit(social_security_ben)
    return  target_income - after_tax_social_security - annuity_inc #income need above guaranteed income

def get_forecast_projection(age, spend_down_age, tax_types, initial_wealth, raw_ctrbs, salary, post_tax_withdrawal, config, after_tax_social_security, target_income):
    #calculate intermediate outputs
    equity_allocation_over_time, beg_wealth_over_time, end_wealth_over_time = initalize_arrays_that_vary_over_time(age = age,
                                                                                                                    spend_down_age = spend_down_age,
                                                                                                                    tax_types = tax_types, starting_wealth = initial_wealth)
    planning_horizon = spend_down_age - age
    ctrbs = convert_contributions(raw_ctrbs, tax_types, salary)
    percentiles = config

    #Set initial wealth at time 0
    for i in range(100):
        beg_wealth_over_time[0][i][:] = initial_wealth

    #Define accumalation and decumalation period
    accum_period = max(ret_age - age, 0)
    decum_period = min(spend_down_age - age, spend_down_age - ret_age)

    #initialize income over time array and objective function constraint
    income_over_time = np.zeros((decum_period, num_sim_runs, len(tax_types)))
    #Forecast Accumulation Period
    for n in range(accum_period):
        calculated_age = age + n
        m = lookup_closest_model_port(equity_allocation_over_time, n)
        #calculte
        end_wealth_over_time[n][:][:] = accumulate(age = calculated_age, ret_age = ret_age,
                                                        ctrbs = ctrbs, starting_wealth = beg_wealth_over_time[n][:][:],
                                                        model_port = m, projection_year = n,
                                                        tax_types = tax_types, num_sim_runs = num_sim_runs)

        #Update beginning of year values for account balances
        beg_wealth_over_time[n+1][:][:] = end_wealth_over_time[n][:][:]

    #Forecast Decumulation Period
    for n in range(decum_period):
        calculated_age = age + n + accum_period
        m = lookup_closest_model_port(equity_allocation_over_time, n + accum_period)
        #post_tax_withdrawal = 30000 #can vary over time
        end_wealth_over_time[n + accum_period][:][:], income_over_time[n][:][:] = decumulate(age = calculated_age, ret_age = ret_age,
                                                                                post_tax_withdrawal = post_tax_withdrawal,
                                                                                starting_wealth = beg_wealth_over_time[n + accum_period][:][:],
                                                                                model_port = m, projection_year = n + accum_period,
                                                                                tax_types = tax_types, num_sim_runs = num_sim_runs,after_tax_social_security = after_tax_social_security)

        #Update beginning of year values for account balances
        if n + 1 < decum_period:
            beg_wealth_over_time[n + accum_period +1][:][:] = end_wealth_over_time[n + accum_period][:][:]

    #calculate wealth at specified percentiles
    percentiles = [30, 50]
    wealth_over_time_at_specified_percentile = np.zeros((accum_period+decum_period, len(percentiles), len(tax_types)))
    for n in range(accum_period + decum_period):
        for p in range(0, len(percentiles)):
            wealth_over_time_at_specified_percentile[n][p][:] = np.percentile(end_wealth_over_time[n][:][:], percentiles[p])
        #print(wealth_over_time_at_specified_percentile[n][0][:])

    #calculate income at specified percentiles
    income_over_time_at_specified_percentile = np.zeros((decum_period, len(percentiles), len(tax_types)))
    for n in range(decum_period):
        for p in range(0, len(percentiles)):
            income_over_time_at_specified_percentile[n][p][:] = np.percentile(income_over_time[n][:][:], percentiles[p])
        #print(income_over_time_at_specified_percentile[n][0][:])

    ruin_probability = 0.3

    #Nested Dictionary
    output_dictionary = {"Heuristics" : {"Ruin_Probability": ruin_probability},
                        "Income": {"Percentile_1" : income_over_time_at_specified_percentile[:,0,:], "Percentile_2" : income_over_time_at_specified_percentile[:,1,:]},
                        "Wealth": {"Percentile_1" : wealth_over_time_at_specified_percentile[:,0,:], "Percentile_2" : wealth_over_time_at_specified_percentile[:,1,:]}}


    return output_dictionary  #dictionary of output including wealth over time at specified percentiles, income over time at specified percentiles, ruin probability

if test == True:
    spend_down_age = 80 #covered in app.py
    age = 55 #covered in app.py
    ret_age = 65 #covered in app.py
    tax_types = ['Traditional'] #covered in app.py
    planning_horizon = spend_down_age - age #can be covered in app.py
    ctrbs = [5000] #covered in app.py
    raw_ctrbs = [5000] #covered in app.py
    initial_wealth = [50000] #covered in app.py
    salary = 55000 #covered in app.py
    config = [30, 50] #to be added in app.py
    social_security_ben = 25000 #covered in app.py
    target_income = 45000 #covered in app.py

const = {'type': 'ineq', 'fun':const_function}
after_tax_social_security = calc_after_tax_social_security_benefit(social_security_ben)
post_tax_withdrawal = determine_post_tax_withdrawal(social_security_ben, target_income)
output_dictionary = get_forecast_projection(age, spend_down_age, tax_types, initial_wealth, raw_ctrbs, salary, post_tax_withdrawal, config, after_tax_social_security, target_income)
print(output_dictionary['Income']['Percentile_1'])




