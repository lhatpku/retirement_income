import numpy as np

def initalize_arrays(profile, config,num_sim_runs = 100):

    initial_wealth = profile['account']['balance']
    age = profile['age']
    retirement_age = profile['retirement_age']
    spend_down_age = profile['spend_down_age']
    planning_horizon = spend_down_age - age + 1
    annuity_start_age = profile['annuity']['start_age']
    annuity_benefit = profile['annuity']['benefit']
    ss_start_age = profile['social_security']['claim_age']
    ss_benefit = profile['social_security']['benefit']

    dfGlidePath = config['glidepath']

    #Initalize glide path
    equity_allocation_over_time = np.zeros(planning_horizon)
    for n in range(planning_horizon):
        equity_allocation_over_time[n] = dfGlidePath.EquityLevel[age + n]

    #define arrays of values that will vary over time
    beg_wealth_over_time = np.zeros((planning_horizon, num_sim_runs))
    end_wealth_over_time = np.zeros((planning_horizon,num_sim_runs))
    ss_income = np.zeros(planning_horizon)
    annuity_income = np.zeros(planning_horizon)

    #Set initial wealth at time 0
    for i in range(num_sim_runs):
        beg_wealth_over_time[0][i] = initial_wealth

    # SS benefit
    ss_income[ss_start_age - age: ] = ss_benefit
    annuity_income[annuity_start_age - age:] = annuity_benefit

    ## for 1/T* approach
    def calculate_conditional_life_estimate(profile, config):
        age = profile['age']
        gender = profile['gender']
        spend_down_age = profile['spend_down_age']
        dfMortTbl = config['mortality_table']
        percentile = 0.5 #static for now
        planning_horizon = spend_down_age - age + 1
        conditional_life_estimate_over_time = np.zeros(planning_horizon)

        ## Calculate the conditional life expectancy given each projected age
        for n in range(planning_horizon):
            starting_age = age + n
            SurvivalProbability = []
            tPx = 1
            for x in range(120-starting_age):
                tPx = tPx * (1 - dfMortTbl.Male[starting_age + x]) if gender == 'Male' else tPx * (1 - dfMortTbl.Female[starting_age + x])
                SurvivalProbability.append(tPx)
                    
            conditional_life_estimate_over_time[n]= starting_age + 1 + sum(1 for px in SurvivalProbability if px > percentile)

        return conditional_life_estimate_over_time

    # Spending curve boundary vectors
    spending_boundary_curve_vec = np.zeros(planning_horizon)
    a_param = 1/pow((spend_down_age-retirement_age)/2,2)
    a = (1 - profile['target']['minimum_ratio']) * a_param
    b = profile['target']['minimum_ratio']
    for n in range(len(spending_boundary_curve_vec)):
        if n + age >= retirement_age:
            spending_boundary_curve_vec[n] = a * pow((n + age - (spend_down_age+retirement_age)/2),2) + b

    # intialize 3 dynamic spending methods
    dynamic_spending_one_over_t_vec = np.zeros(planning_horizon)
    dynamic_spending_one_over_t_star_vec = np.zeros(planning_horizon)
    dynamic_spending_liability_ratio_vec = np.zeros(planning_horizon)
    dynamic_spending_methods_dictionary = {} #store all dynamic spending method vectors

    conditional_life_estimate_over_time = calculate_conditional_life_estimate(profile, config)
    
    for n in range(len(dynamic_spending_one_over_t_vec)):
        calculated_age = age + n    
        if calculated_age >= retirement_age:
            dynamic_spending_one_over_t_vec[n] = 1 / (spend_down_age + 1 - calculated_age)
            dynamic_spending_one_over_t_star_vec[n] = 1 / (min(conditional_life_estimate_over_time[n], spend_down_age + 1) - calculated_age)
            dynamic_spending_liability_ratio_vec[n] = spending_boundary_curve_vec[n] / np.sum(spending_boundary_curve_vec[n:])
        
    
    dynamic_spending_methods_dictionary['1/T'] = dynamic_spending_one_over_t_vec
    dynamic_spending_methods_dictionary['1/T*'] = dynamic_spending_one_over_t_star_vec
    dynamic_spending_methods_dictionary['Liability_Ratio'] = dynamic_spending_liability_ratio_vec

    initial_vector = {}
    initial_vector['equity_allocation'] = equity_allocation_over_time
    initial_vector['wealth_begin'] = beg_wealth_over_time
    initial_vector['wealth_end'] = end_wealth_over_time
    initial_vector['ss_income'] = ss_income
    initial_vector['annuity_income'] = annuity_income
    initial_vector['spending_curve'] = spending_boundary_curve_vec
    initial_vector['dynamic_spending_dict'] = dynamic_spending_methods_dictionary

    return initial_vector