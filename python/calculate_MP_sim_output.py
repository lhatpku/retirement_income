import os
import pandas as pd
import numpy as np

#https://stackoverflow.com/questions/46950173/python-looping-through-directory-and-saving-each-file-using-filename-as-data-fr

def load_sim_runs():
    #Create list of data frames for each asset class simulation return file
    root = '../data/Simulation_Returns'
    ddict = {}
    asset_class_names = []
    for file in os.listdir(root):
        name = os.path.splitext(file)[0]
        asset_class_names.append(name)
        ddict[name] = pd.read_csv(os.path.join(root, file),header = None)
        #print(name)
    #print(ddict['Emerging Markets Bond'].iat[1,0])
    return ddict

def load_model_portfolios():
    dfModelPorts = pd.read_csv('../data/modelPortfolio.csv', header = None)
    #print(dfModelPorts.iat[0,0])
    return dfModelPorts


def calculate_model_port_sims():
    dfAssetClassSimRuns = load_sim_runs()
    dfModelPorts = load_model_portfolios()
    asset_class_column_ordering = ['Commodities','Global ex-US REIT','US REIT','Emerging Markets Equity','Developed Markets Large Cap',
                                  'US Small Cap Growth','US Small Cap Value','US Large Cap Growth','US Large Cap Value',
                                  'Global ex-US Small Cap','Emerging Markets Bond','Developed Markets Bond','US High Yield Bond',
                                  'US Treasury Bond - 5 Plus Years','US Treasury Bond - 1 to 5 Years','US Corporate Bond',
                                  'US Agency Bond','US Mortgage Backed Bond','US Municipal Bond','TIPS','Short-Term']
    no_model_ports = 100
    no_sim_runs = 100
    no_sim_years = 100

    #specify empty array to contain simulated model portfolio returns
    ModelPortReturnsBySimAndYear = np.zeros((no_model_ports, no_sim_runs, no_sim_years)) #model portfolios, sim runs, and years
    for model_port in range(no_model_ports):
        for sim_run in range(no_sim_runs):
            for sim_year in range(no_sim_years):
                for asset_class in asset_class_column_ordering:
                    index_value = int(asset_class_column_ordering.index(asset_class))
                    weighted_asset_class_sim_return = (
                    dfAssetClassSimRuns[asset_class].iat[sim_run,sim_year] *
                    dfModelPorts.iat[model_port,index_value])
                    ModelPortReturnsBySimAndYear[model_port][sim_run][sim_year] = (
                    ModelPortReturnsBySimAndYear[model_port][sim_run][sim_year] + weighted_asset_class_sim_return)

    #save the output
    np.save('../data/model_portfolio_output.npy',ModelPortReturnsBySimAndYear)

    return ModelPortReturnsBySimAndYear
calculate_model_port_sims()
