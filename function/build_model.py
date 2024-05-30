# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 19:40:17 2024

@author: vicke
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 19:47:25 2024

@author: vicke
"""

# from function.cal_cost_df import Cal_lcoe_fromDF, Initial_PP_lcoeDF, Initial_CCS_lcoeDF, Add_BE_first_DF, Add_BE_after_DF, Add_flexi_first_DF, Add_flexi_after_DF, Add_CCS_DF, Add_BECCS_first_DF, Add_BECCS_after_DF, Add_Retire_DF
# from function.cal_cost_value import Add_BE_first_Value, Add_BE_after_Value, Add_flexi_first_Value, Add_flexi_after_Value, Add_CCS_Value, Add_BECCS_first_Value, Add_BECCS_after_Value, Add_Retire_Value
# from function.cal_emiss import Emiss_PP, Emiss_BE, Emiss_CCS, Emiss_BECCS, Emiss_Retire
from function.cal_emiss1 import cal_emiss
from function.cal_cost import cal_cost
from function.cal_profit import cal_profit
import gurobipy as gp
from gurobipy import GRB
import pandas as pd

scale_emiss = pow(10,6) # million tonne
scale_profit = pow(10,9) # billion dollars
scale_elec = pow(10, 6) # Million kWh
scale_bio = pow(10,6) # GWh

def build_model(name, power_station_id, PPs_hours, InsCapacity, 
                lon, lat, operateYear, set_retrofitYr,
                ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                y_opt, take, res_point_id, 
                resources, power2res, distance, EMISS_GOAL, gap_set, 
                BioSupply, columnName, unitCoal, flex,
                be, ccs, retire, ELEC_GOAL, elecPrice, TIMELIMITS):
    
    ppNum_scale = len(power_station_id)
    
    m = gp.Model(name)
    m.setParam('MIPGap', gap_set)
    m.setParam('Timelimit', 600)
    # m.params.NonConvex = 2
    
    # create decision variables for how much resource through which combination
    take = m.addVars(power2res, lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name='x')
    
    # create variable for retrofit or not
    y_flex = m.addVars(power_station_id, vtype=GRB.BINARY, name="flexible")
    y_be = m.addVars(power_station_id, vtype=GRB.BINARY, name="be")
    y_ccs = m.addVars(power_station_id, vtype=GRB.BINARY, name="ccs")
    y_retire = m.addVars(power_station_id, vtype=GRB.BINARY, name='compulsory retirement')
    
    # create variable for capacity factor
    cf = m.addVars(power_station_id, lb=0.0, ub=1.7, vtype=GRB.CONTINUOUS, name="capacity factor")
    
    # objective function
    profit = 0.
    for p in power_station_id:
        # calculate emission reduction
        y_be_p_past = be[p][0]
        y_ccs_p_past = ccs[p][0]
        y_retire_p_past = retire[p][0]
        # print(p)

        # cal_profit(y_flex_p, y_be_p, y_ccs_p, y_retire_p, cf_p, ori_lcoeFrame_p, capacity_p, hours_p, sum_j_xij_kwh,  sum_j_DBxij, dccs_p, operateYear_p, set_retrofitYr, columnName)
        profit_p = cal_profit(y_flex[p], y_be[p], y_ccs[p], y_retire[p], cf[p], ori_lcoeFrame[p], InsCapacity[p], PPs_hours[p], 
                          take.sum(p, '*'),  take.prod(distance, p, "*"), dccs[p], operateYear[p], set_retrofitYr, 'Value', elecPrice)
        
        profit = profit + profit_p / scale_profit # billion dollar
    
    # profit = profit/profitScale
    m.setObjective(profit, GRB.MAXIMIZE) 
    m.update()
    print('finish objective update')
 
    # constraints 
    # 1. supply: biomass resource constraints
    for r in res_point_id:
        m.addRange(take.sum('*', r) / scale_bio, 0, resources[r] / scale_bio, 'biomass upper bound')
        
    # 2. demand: capacity_p * hours_p * cf_p >= sum_j_xij_kwh
    for p in power_station_id:
        m.addConstr((take.sum(p, '*') / scale_bio  <= PPs_hours[p] * InsCapacity[p] * cf[p] * 0.9 / scale_bio), "demand bound") # neccessary
    
    # 3. carbon emission constraints
    emiss_sum = 0.
    for p in power_station_id:
        y_be_p_past = be[p][0]
        y_ccs_p_past = ccs[p][0]     
        tmp_emiss = cal_emiss(y_be_p_past, y_be[p], y_ccs_p_past, y_ccs[p], y_retire[p], cf[p], InsCapacity[p], 
                  PPs_hours[p], take.sum(p, '*'),  take.prod(distance, p, "*"), unitCoal[p])
        # print(tmp_emiss)
        emiss_sum = emiss_sum + tmp_emiss / scale_emiss # million tonnes CO2   
        # print('emiss: %.f' % p)
    
    m.addConstr((emiss_sum <= EMISS_GOAL / scale_emiss), 'emission target')
    m.update()
    
    # 5. electricity constraints
    elec_sum = 0.
    for p in power_station_id:
        elec_sum = elec_sum + InsCapacity[p] * PPs_hours[p] * cf[p] / scale_elec
        # print(elec_sum)
    m.addConstr((elec_sum >= ELEC_GOAL / scale_elec), 'electricity constraint')
    # m.addConstr((elec_sum /ppNum_scale >= ori_elec_sum * 0.5 /ppNum_scale), 'electricity constraint')
    m.update()
    
    # 4. options: 
    M = pow(10,5)
    ## 4.1 flex retrofit: 
    for p in power_station_id:
        m.addConstr((cf[p] >= (1 - M * (y_flex[p] + flex[p][0]))), 'no_flex_retrofit') # if y_flex + past_flex = 0, CF_i = 1
        m.addConstr((cf[p] * PPs_hours[p] >= 1500 * y_flex[p]), 'flex has capacity') # if y_flex = 1, CF_i > 0
        # m.addConstr((cf[p] * PPs_hours[p] <= 3500 * (y_flex[p] + flex[p][0])), 'flex has capacity') # if y_flex = 1, CF_i > 0
    
    ## 4.2 be retrofit:
    for pr in power2res:
        p = pr[0]
        r = pr[1]
        # to reduce the factor of the matrix, divide by 10^6
        m.addConstr((take[(p,r)] / scale_bio <= M * (y_be[p] + be[p][0])), 'no_be_retrofit') # if no retrofit with be, don't transport biomass
        m.addConstr((take[(p,r)] / scale_bio <= M * (1 - y_retire[p])), 'no biomass collection') # if compulsory retirement, don't transport biomass

    ## 4.3 compulsory retirement:
    for p in power_station_id:
        m.addConstr((cf[p] <= 1.7*(1-y_retire[p])), 'no capacity factor') # if plant is compulsory retired, the capacity factor equals to 0
    
    ## 4.4 technology of different technologies:
    for p in power_station_id:      
        m.addConstr((y_flex[p] + flex[p][0] <= 1), 'flexible')
        m.addConstr((y_be[p] + be[p][0] <= 1), 'be')
        m.addConstr((y_ccs[p] + ccs[p][0] <=1), 'ccs')
        m.addConstr((y_retire[p] + retire[p][0] <=1), 'compulsory retirement')
        m.addConstr((y_flex[p] <= (1- y_retire[p])), 'if cr, forbid other choices') 
        m.addConstr((y_be[p] <= (1- y_retire[p])), 'if cr, forbid other choices')
        m.addConstr((y_ccs[p] <= (1- y_retire[p])), 'if cr, forbid other choices')
    
    # ps: close some technology
    # for p in power_station_id:     
    #     m.addConstr((y_retire[p] == 1),'tmp')
        # m.addConstr((y_ccs[p] == 1), 'tmp')
        # m.addConstr((take.sum(p, '*')  == PPs_hours[p] * InsCapacity[p] * cf[p]), 'tmp')
    
    #4. capacity constraints
    # capacity_sum = 0.
    # ori_capacity_sum = 0.
    # for p in power_station_id:
    #     capacity_sum = capacity_sum + InsCapacity[p] * (1-y_retire[p])
    #     ori_capacity_sum = ori_capacity_sum + InsCapacity[p]
    # m.addConstr((capacity_sum >= ori_capacity_sum * 0.6), 'capacity constraint')
    # m.update()
    
    m.optimize()
    # m.computeIIS()
    # m.write('model1.ilp')
    print("model status is: %s" % m.status)
    
    return m, take, y_flex, y_be, y_ccs, y_retire, cf, take