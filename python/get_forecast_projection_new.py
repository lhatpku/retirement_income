import os
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP
from python.calc_tax import calc_income_tax_liability, calc_fica_tax_liability, calc_take_home_income
from python.initialize import initalize_arrays
from python.model_port_helper import calc_model_port_ret_across_sim_runs_at_projection_year, lookup_closest_model_port
import json
from scipy.optimize import minimize

####################
## Accumulate for one year
####################
def accumulate_for_one_year(age, ctrbs, starting_wealth, model_port, projection_year, config,num_sim_runs = 100):
    
    ModelPortReturnsBySimAndYear = calc_model_port_ret_across_sim_runs_at_projection_year(model_port, projection_year,config)

    EOY_wealth = np.zeros(num_sim_runs)

    for i in range(num_sim_runs):
            EOY_wealth[i] = starting_wealth[i] * (1 + ModelPortReturnsBySimAndYear[:,i]) + ctrbs

    return EOY_wealth

####################
## Decumulate for one year
####################
def decumulate_for_one_year(profile, starting_wealth, model_port, projection_year, SS_Income, annuity_Income, config,
                            spending_boundary_at_projection_year, dynamic_spending_ratio_at_projection_year, num_sim_runs = 100):
    
    ModelPortReturnsBySimAndYear = calc_model_port_ret_across_sim_runs_at_projection_year(model_port, projection_year,config)

    EOY_wealth = np.zeros(num_sim_runs)
    after_tax_retirement_income = np.zeros(num_sim_runs)
    income_tax_config = config['income_tax']

    ## Dynamic Spending function
    def determine_target_spending_at_node(profile, config, spending_boundary_at_projection_year, 
                                        dynamic_spending_ratio_at_projection_year,starting_wealth_at_sim_run,
                                        annuity_Income, SS_Income):
        # target = profile['target']['fixed']
        # income_tax_assumption = 0.25 #used to determine the after tax dynamic spending target at each node
        minimum_spending_boundary = profile['target']['essential']
        maximum_spending_boundary = profile['target']['discretional']
        minimum_boundary = minimum_spending_boundary * spending_boundary_at_projection_year #lower boundary
        maximum_boundary = maximum_spending_boundary * spending_boundary_at_projection_year #upper boundary

        ## Dynamic amount is the product of the starting account balance and the ratio following from the specified method
        # dynamic_amount = starting_wealth_at_sim_run * dynamic_spending_ratio_at_projection_year * (1 - income_tax_assumption) + annuity_Income + SS_Income if starting_wealth_at_sim_run > 0 else 0
        '''
        Apply tax model to accounts to calculate dynamical spending amount
        '''
        if profile['account']['type'] == 'Traditional': 
            dynamic_amount_tax = calc_income_tax_liability(starting_wealth_at_sim_run * dynamic_spending_ratio_at_projection_year, SS_Income, income_tax_config)
        else:
            dynamic_amount_tax = 0
        dynamic_amount = starting_wealth_at_sim_run * dynamic_spending_ratio_at_projection_year + annuity_Income + SS_Income - dynamic_amount_tax if starting_wealth_at_sim_run > 0 else 0
        
        ## Dynamic target is higher than lower boundary if enough account balance
        dynamic_target = max(minimum_boundary, min(maximum_boundary, dynamic_amount))

        return dynamic_target

    ## Define the optimization function 
    def objectiveFunction(pre_tax_withdrawal,target,accountType):
        if accountType == 'Traditional':
            income_tax_liability = calc_income_tax_liability(pre_tax_withdrawal, SS_Income, income_tax_config)
        else:
            income_tax_liability = 0
        return abs(pre_tax_withdrawal + SS_Income + annuity_Income - income_tax_liability - target)

    for i in range(num_sim_runs):
        target = determine_target_spending_at_node(profile, config, spending_boundary_at_projection_year, 
                                        dynamic_spending_ratio_at_projection_year, starting_wealth[i],
                                        annuity_Income, SS_Income)
        
        if starting_wealth[i] < 100:
            optimized_pre_tax_withdrawal = starting_wealth[i]
        else: 
            solution = minimize(fun=lambda x: objectiveFunction(x,target,profile['account']['type']), x0 = 0,method='SLSQP',bounds=[(0,starting_wealth[i])])
            optimized_pre_tax_withdrawal = solution.x

        EOY_wealth[i] = max(starting_wealth[i] - optimized_pre_tax_withdrawal,0) * (1 + ModelPortReturnsBySimAndYear[:,i])
        
        if profile['account']['type'] == 'Traditional':
            income_tax_liability = calc_income_tax_liability(optimized_pre_tax_withdrawal, SS_Income, income_tax_config)
        else:
            income_tax_liability = 0
        after_tax_retirement_income[i] = optimized_pre_tax_withdrawal + SS_Income + annuity_Income - income_tax_liability

    return EOY_wealth, after_tax_retirement_income

####################
## Forecast Projection
####################
def get_forecast_projection(profile, config, forecast_config, num_sim_runs=100):
    
    #calculate initial array and intermediate output
    initial_vector = initalize_arrays(profile, config, num_sim_runs)

    equity_allocation_over_time = initial_vector['equity_allocation']
    beg_wealth_over_time = initial_vector['wealth_begin']
    end_wealth_over_time = initial_vector['wealth_end']
    ss_income = initial_vector['ss_income']
    annuity_income = initial_vector['annuity_income']
    spending_boundary_curve_vec = initial_vector['spending_curve']
    dynamic_spending_methods_dictionary = initial_vector['dynamic_spending_dict']
    
    #calculate intermediate outputs
    age = profile['age']
    spend_down_age = profile['spend_down_age']
    retirement_age = profile['retirement_age']
    planning_horizon = spend_down_age - age + 1
    ctrbs = profile['account']['contribution'] * profile['salary']
    percentiles = forecast_config['percentiles']
    essential_target = profile['target']['essential']
    discretional_target = profile['target']['discretional']
    dynamic_spending_method = str(profile['spending_strategy'])
    spending_curve_vec = dynamic_spending_methods_dictionary[dynamic_spending_method]

    age_vec = list(range(age,(spend_down_age+1)))

    #initialize income over time array
    income_over_time = np.zeros((planning_horizon, num_sim_runs))
        
    #Forecast Accumulation and Decumulation period
    for n in range(planning_horizon):
        calculated_age = age + n
        model_port = lookup_closest_model_port(equity_allocation_over_time, n)

        if calculated_age < retirement_age:
            end_wealth_over_time[n][:] = accumulate_for_one_year(age = calculated_age, ctrbs = ctrbs, starting_wealth = beg_wealth_over_time[n][:],
                                                        model_port = model_port, projection_year = n,
                                                        config=config, num_sim_runs = num_sim_runs)
        else:
            end_wealth_over_time[n][:],income_over_time[n][:] = decumulate_for_one_year(profile = profile, starting_wealth = beg_wealth_over_time[n][:],
                                                         model_port = model_port, projection_year = n,
                                                         SS_Income = ss_income[n], annuity_Income = annuity_income[n], 
                                                         config=config, spending_boundary_at_projection_year = spending_boundary_curve_vec[n], 
                                                         dynamic_spending_ratio_at_projection_year = spending_curve_vec[n], num_sim_runs = num_sim_runs)
        if n < planning_horizon - 1:
            beg_wealth_over_time[n+1][:] = end_wealth_over_time[n][:]

    #Nested Dictionary output
    income_output_list = []
    wealth_output_list = []

    for p in range(0, len(percentiles)):
        wealth_over_time_at_specified_percentile = np.zeros(planning_horizon)
        income_over_time_at_specified_percentile = np.zeros(planning_horizon)
        for n in range(planning_horizon):
            wealth_over_time_at_specified_percentile[n] = np.percentile(beg_wealth_over_time[n][:], percentiles[p])
            income_over_time_at_specified_percentile[n] = np.percentile(income_over_time[n][:], percentiles[p])
        income_output_list.append({'percentile':percentiles[p],'income':list(income_over_time_at_specified_percentile)})
        wealth_output_list.append({'percentile':percentiles[p],'wealth':list(wealth_over_time_at_specified_percentile)})


    # RuinProbability = calc_probability_of_ruin(profile, config, end_wealth_over_time, num_sim_runs=100)
    output_dictionary = {"Heuristics" : {"Ruin_Probability": 0},
                        "Income": income_output_list,
                        "Wealth": wealth_output_list,
                        "Age":age_vec,
                        "target_upperBound":list(discretional_target*spending_boundary_curve_vec),
                        "target_lowerBound":list(essential_target*spending_boundary_curve_vec),
                        "profile":{"income_start_index":max(retirement_age-age,0)},
                        "spending_strategy":profile['spending_strategy']}

    return output_dictionary