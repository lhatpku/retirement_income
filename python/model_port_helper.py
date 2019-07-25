import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

def calc_model_port_ret_across_sim_runs_at_projection_year(model_port_id,projection_year,config,num_sim_runs=100):

    mp_asset_class_column_ordering = config['asset_class_order']
    dfModelPorts = config['modelportfolios']
    DFs_asset_class_sim_run = config['simulation_returns']

    asset_class_sim_run_matrix = np.zeros((len(mp_asset_class_column_ordering), num_sim_runs))

    #Determine asset class sim run 21 x 100 matrix
    for i, name in enumerate(mp_asset_class_column_ordering):
        asset_class_sim_run_matrix[i][:] = DFs_asset_class_sim_run[name].iloc[:,projection_year]

    #Determine model_portfolio asset allocation weights 1 x 21 matrix
    model_port_asset_class_matrix = dfModelPorts.iloc[[model_port_id-1]]
    
    #Calculate model portfolio simulated output across all sim runs for specified projection year
    model_port_sim_run_output = np.matmul(model_port_asset_class_matrix, asset_class_sim_run_matrix)
    
    return model_port_sim_run_output

def lookup_closest_model_port(equity_allocation_over_time, projection_year):
    temp = round(equity_allocation_over_time[projection_year] * 100 / 0.01) * 0.01
    model_port = Decimal(temp).to_integral_value(rounding = ROUND_HALF_UP)
    return model_port

def calc_granular_model_port_allocation(profile, config):
    
    dfGlidePath = config['glidepath']    
    dfModelPorts = config['modelportfolios']
    age = profile['age']
    spend_down_age = profile['spend_down_age']
    planning_horizon = spend_down_age - age + 1
    equity_asset_class_order = ['Commodities','Global ex-US REIT','US REIT','Emerging Markets Equity','Developed Markets Large Cap',
                              'US Small Cap Growth','US Small Cap Value','US Large Cap Growth','US Large Cap Value',
                              'Global ex-US Small Cap']
    bond_asset_class_order = ['Emerging Markets Bond','Developed Markets Bond','US High Yield Bond',
                              'US Treasury Bond - 5 Plus Years','US Treasury Bond - 1 to 5 Years','US Corporate Bond',
                              'US Agency Bond','US Mortgage Backed Bond','US Municipal Bond','TIPS','Short-Term']

    equity_allocation_over_time = np.zeros(planning_horizon)
    for n in range(planning_horizon):
        equity_allocation_over_time[n] = dfGlidePath.EquityLevel[age + n]

    asset_allocation_dictionary = {}
    for n in range(planning_horizon):
        calculated_age = age + n
        model_port = lookup_closest_model_port(equity_allocation_over_time, n)
        allocations = dfModelPorts.iloc[[model_port-1]]
        equity_allocations = allocations.iloc[:, 0:10].values.tolist()[0]
        bond_allocations = allocations.iloc[:,10:].values.tolist()[0]
        equity_dictionary = dict(zip(equity_asset_class_order, equity_allocations))
        bond_dictionary = dict(zip(bond_asset_class_order, bond_allocations))
        allocation_plot_list = []
        allocation_plot_list.append({"id": "0.0", "name": "Portfolio", "parent": ""})
        allocation_plot_list.append({"id": "1.0", "name": "Bond", "parent": "0.0"})
        allocation_plot_list.append({"id": "1.1", "name": "Equity", "parent": "0.0"})
        count = 0

        for key in bond_dictionary:
            allocation_plot_list.append({"id": f'2.{count}', "name": key, "parent": "1.0","value": bond_dictionary[key]})
            count = count + 1

        for key in equity_dictionary:
            allocation_plot_list.append({"id": f'2.{count}', "name": key, "parent": "1.1","value": equity_dictionary[key]})
            count = count + 1

        asset_allocation_dictionary.update({str(calculated_age): allocation_plot_list})

    return asset_allocation_dictionary