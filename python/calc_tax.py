def calc_income_tax_liability(pre_tax_income, social_security_benefit, config):
    agi = pre_tax_income
    agi_after_deduction = max(agi - config['standard_deduction'],0)
    tax_bracket_list = config['tax_bracket']
    income_tax_liability = 0
    for tax_bracket in tax_bracket_list:
        income_tax_liability = income_tax_liability + tax_bracket['rate'] * min(max(agi_after_deduction - tax_bracket['lower_bracket'],0),tax_bracket['upper_bracket'] - tax_bracket['lower_bracket'])
    return income_tax_liability


def calc_fica_tax_liability(gross_income,config):
    return gross_income * (config['social_security']['rate'] + config['medicare']['rate'])


def calc_take_home_income(gross_income,pre_tax_contrib,post_tax_contrib,income_tax_config,fica_config):
    fica_tax_liability =  calc_fica_tax_liability(gross_income,fica_config)
    pre_tax_income = gross_income - pre_tax_contrib * gross_income
    income_tax_liability = calc_income_tax_liability(pre_tax_income, 0, income_tax_config)
    return gross_income - fica_tax_liability - income_tax_liability - pre_tax_contrib * gross_income - post_tax_contrib * gross_income
