import os
import pandas as pd
import numpy as np
import json
from flask import Flask, jsonify, render_template, flash, request, redirect
from python.calc_spend_down_age import calc_spend_down_age
from python.calc_Social_Security import calc_social_security_benefit
from python.calc_tax import calc_income_tax_liability, calc_fica_tax_liability, calc_take_home_income
from python.load_data import load_glide_path, load_model_portfolios, load_sim_runs, load_mort_tbl, load_SPIA_rates
from python.get_forecast_projection_new import get_forecast_projection
from python.model_port_helper import calc_granular_model_port_allocation

app = Flask(__name__)

root_loc = 'data'
#######################
# Tax Input
#######################
fica_loc = os.path.join(root_loc,'fica_tax.json')
income_tax_loc = os.path.join(root_loc,'income_tax.json')

fica_dict = json.loads(open(fica_loc).read())
income_tax_dict = json.loads(open(income_tax_loc).read())
#######################
# Other Configs
#######################
dfGlidePath = load_glide_path(root_loc)
dfModelPorts = load_model_portfolios(root_loc)
dfMortTbl = load_mort_tbl(root_loc)
dfSPIA_rates = load_SPIA_rates(root_loc)
DFs_asset_class_sim_run, asset_class_sim_run_ordering = load_sim_runs(root_loc)

mp_asset_class_column_ordering = ['Commodities','Global ex-US REIT','US REIT','Emerging Markets Equity','Developed Markets Large Cap',
                              'US Small Cap Growth','US Small Cap Value','US Large Cap Growth','US Large Cap Value',
                              'Global ex-US Small Cap','Emerging Markets Bond','Developed Markets Bond','US High Yield Bond',
                              'US Treasury Bond - 5 Plus Years','US Treasury Bond - 1 to 5 Years','US Corporate Bond',
                              'US Agency Bond','US Mortgage Backed Bond','US Municipal Bond','TIPS','Short-Term']
config = {}
config['glidepath'] = dfGlidePath
config['modelportfolios'] = dfModelPorts
config['simulation_returns'] = DFs_asset_class_sim_run
config['asset_class_order'] = mp_asset_class_column_ordering
config['income_tax'] = income_tax_dict
config['fica_tax'] = fica_dict
config['mortality_table'] = dfMortTbl
config['SPIA_rates'] = dfSPIA_rates

#######################
# Forecast Config
#######################
forecast_config = {}
forecast_config['percentiles'] = [30,50,70]
################## Routes ######################
@app.route('/')
def index():
    spend_down_age = calc_spend_down_age(30,'Male',0.7)
    ss_benefit = round(calc_social_security_benefit(100000,65))
    default_take_home_income = round(calc_take_home_income(100000,0,0,income_tax_dict,fica_dict))
    return render_template("index.html",spen_down_age = spend_down_age,ss_benefit=ss_benefit,take_home_income=default_take_home_income)

@app.route('/process',methods=['POST'])
def process():
    # Initialize the inputs
    profile = {}
    # Assign basic profile information
    profile['name'] = request.form['name']
    profile['gender'] = request.form['gender']
    profile['age'] = int(request.form['age'])
    profile['salary'] = float(request.form['salary'])
    profile['retirement_age'] = int(request.form['retirement_age'])
    profile['account'] = {}
    profile['account']['balance'] = float(request.form['manageable_balance'])
    profile['account']['contribution'] = float(request.form['manageable_contrib'])/100
    profile['account']['type'] = request.form['manageable_tax']
    profile['social_security'] = {}
    profile['social_security']['claim_age'] = int(request.form['ss_claim_age'])
    profile['social_security']['benefit'] = float(request.form['ss_benefit'])
    profile['annuity'] = {}
    profile['annuity']['start_age'] = int(request.form['annuity_start_age'])
    profile['annuity']['benefit'] = float(request.form['annuity_benefit'])
    # Assign spend down age
    profile['spend_down_age'] = int(request.form['spend_down_age'])
    # Assign target information
    profile['target'] = {}
    profile['target']['essential'] = float(request.form['non_dis_target'])
    profile['target']['discretional'] = float(request.form['dis_target'])
    profile['target']['minimum_ratio'] = float(request.form['minimum_spending_ratio'])/100
    profile['target']['maximum_ratio'] = 1.5 ##static for now
    profile['target']['fixed'] = (profile['target']['discretional'] + profile['target']['essential']) / 2

    if request.form['spending_strategy'] == '1/T':
        profile['spending_strategy'] = '1/T'
    elif request.form['spending_strategy'] == '1/T*':
        profile['spending_strategy'] = '1/T*'
    else:
        profile['spending_strategy'] = 'Liability_Ratio'

    forecast_output = get_forecast_projection(profile, config, forecast_config)
    asset_allocation_tiers = calc_granular_model_port_allocation(profile, config)

    output = {**forecast_output,'portfolio':asset_allocation_tiers}

    return jsonify(output)


@app.route('/target',methods=['POST'])
def target():
    salary = float(request.form['salary'])
    contribution = float(request.form['contribution'])/100
    tax_type = request.form['tax']
    if tax_type == 'Traditional':
        pre_tax_contrib = contribution
        post_tax_contrib = 0
    else:
        pre_tax_contrib = 0
        post_tax_contrib = contribution
    replacement_1 = float(request.form['replacement_1'])/100
    replacement_2 = float(request.form['replacement_2'])/100

    take_home_income = round(calc_take_home_income(salary,pre_tax_contrib,post_tax_contrib,income_tax_dict,fica_dict))
    return jsonify({'target_0':take_home_income,'target_1':take_home_income * replacement_1,'target_2':take_home_income * replacement_2})

@app.route('/spenddown',methods=['POST'])
def spend_down():
    confidence_level = float(request.form['confidence_level'])/100
    gender = request.form['gender']
    age = int(request.form['age'])

    spend_down_age = calc_spend_down_age(age,gender,confidence_level)
    return jsonify({'spend_down_age':spend_down_age})

@app.route('/spendcurve',methods=['POST'])
def spend_curve():
    confidence_level = float(request.form['confidence_level'])/100
    gender = request.form['gender']
    age = int(request.form['age'])
    salary = float(request.form['salary'])
    contribution = float(request.form['contribution'])/100
    tax_type = request.form['tax']

    if tax_type == 'Traditional':
        pre_tax_contrib = contribution
        post_tax_contrib = 0
    else:
        pre_tax_contrib = 0
        post_tax_contrib = contribution
    replacement_1 = float(request.form['replacement_1'])/100
    replacement_2 = float(request.form['replacement_2'])/100

    take_home_income = round(calc_take_home_income(salary,pre_tax_contrib,post_tax_contrib,income_tax_dict,fica_dict))
    spend_down_age = calc_spend_down_age(age,gender,confidence_level)

    return jsonify({'spend_down_age':spend_down_age,'target_0':take_home_income,'target_1':take_home_income * replacement_1,'target_2':take_home_income * replacement_2})

@app.route('/social_security',methods=['POST'])
def social_security():
    salary = float(request.form['salary'])
    claim_age = int(request.form['claim_age'])

    ss_benefit = round(calc_social_security_benefit(salary,claim_age))
    return jsonify({'social_security_benefit':ss_benefit})

if __name__ == "__main__":
    app.run(debug=False)
