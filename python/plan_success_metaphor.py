def calc_probability_of_ruin(profile, config, wealth_over_time, num_sim_runs=100):
    #mortality adjusted probability of ruin
    age = profile['age']
    retirement_age = profile['retirement_age']
    wealth_over_time_decumulation_only = wealth_over_time[retirement_age - age:,:]

    def calc_tPx(profile, config):
        dfMortTbl = config['mortality_table']
        gender = profile['gender']
        retirement_age = profile['retirement_age']

        #Calculate Survival Probability over Decumulation Period
        SurvivalProbability = []
        tPx = 1
        for x in range(120 - retirement_age):
            if gender == 'Male':
                tPx = tPx * (1 - dfMortTbl.Male[x + retirement_age])
            else:
                tPx = tPx * (1 - dfMortTbl.Female[x + retirement_age])
            
            SurvivalProbability.append(tPx)
        
        return SurvivalProbability
    
    SurvivalProbability = calc_tPx(profile, config)
    
    ## for each sim run, determine where wealth went to zero and calculate mortality adjusted probability of ruin
    ProbabilityOfRuinVector = []
    for i in range(num_sim_runs):
        temp = np.where(wealth_over_time_decumulation_only[:,i] < 100)
        if any(map(len,temp)):
            year_ran_out_money = temp[0][0]
            ProbabilityOfRuinVector.append(SurvivalProbability[year_ran_out_money])
        else:
            ProbabilityOfRuinVector.append(0)
    
    ProbabilityOfRuin = sum(ProbabilityOfRuinVector)/num_sim_runs
    
    return ProbabilityOfRuin
