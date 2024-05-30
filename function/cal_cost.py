# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 19:58:15 2024

@author: vicke
"""

import numpy as np
import pandas as pd

para = pd.read_csv('function/params_economic.csv', encoding = 'gbk')
para = para.set_index('Parameter')
para_pp_capital = para.loc['PP-capital','Value']
para_pp_fixOM = para.loc['PP-fixOM','Value']
para_pp_variOM = para.loc['PP-variableOM', 'Value']
para_pp_coalCost = para.loc['PP-coalCost', 'Value']
para_be_capital = para.loc['BE-capital', 'Value'] # 变化
para_be_fixOM = para.loc['BE-fixOM', 'Value']
para_be_variOM = para.loc['BE-variableOM', 'Value'] 
para_be_purchaseCost = para.loc['BE-purchaseCost', 'Value'] # 变动
para_be_pretreatCost = para.loc['BE-pretreatCost', 'Value'] # 变动
para_be_trans1 = para.loc['BE-transportCost1', 'Value']
para_be_trans2 = para.loc['BE-transportCost2', 'Value']
para_CCS_capital = para.loc['CCS-capital', 'Value'] # 变动
para_CCS_captureCost = para.loc['CCS-captureCost', 'Value'] # 变动
para_CCS_transCost = para.loc['CCS-transportCost', 'Value'] # 变动
para_CCS_storageCost = para.loc['CCS-storageCost', 'Value'] # 变动
r = 1.05
# r = 1.03
# r = 1.08
lifespan = 40
scale_Bio = pow(10,9)

def updateParas(columnName):
    # Parameters
    para = pd.read_csv('function/params_economic.csv', encoding = 'gbk')
    para = para.set_index('Parameter')
    para_be_capital = para.loc['BE-capital', columnName]   
    para_be_purchaseCost = para.loc['BE-purchaseCost', columnName]    
    para_be_pretreatCost = para.loc['BE-pretreatCost', columnName]   
    para_CCS_capital = para.loc['CCS-capital', columnName] 
    para_CCS_captureCost = para.loc['CCS-captureCost', columnName] 
    para_CCS_transCost = para.loc['CCS-transportCost', columnName]    
    para_CCS_storageCost = para.loc['CCS-storageCost', columnName] 
    return [para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, 
            para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost]

def cal_cost(y_flex_p, y_be_p, y_ccs_p, y_retire_p, cf_p, ori_lcoeFrame_p, 
             capacity_p, hours_p, sum_j_xij_kwh,  sum_j_DBxij, dccs_p, 
             operateYear_p, set_retrofitYr, columnName):
    
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
    
    #===== capital cost ===========
    add_Cap_Flex = para_pp_capital * capacity_p * 0.1 # flex
    add_Cap_BE = para_be_capital * capacity_p # be
    add_Cap_CCS = para_CCS_capital * capacity_p # carbon capture
    
    #===== fuel cost ===========
    fuel_coal = (capacity_p * hours_p * cf_p - sum_j_xij_kwh) * para_pp_coalCost/pow(10,3)
    fuel_be = (para_be_purchaseCost + para_be_pretreatCost + para_be_trans2) * sum_j_xij_kwh/pow(10,3) + sum_j_DBxij * para_be_trans1 / pow(10,3)
    
    #====== OM cost ========
    # OM_PP = (para_pp_fixOM + para_pp_variOM) * capacity_p
    OM_BE = (para_be_fixOM + para_be_variOM) * capacity_p    
    
    Emiss_CO2 = capacity_p * hours_p * cf_p * 0.801 / pow(10,3)
    add_OM_CCS = Emiss_CO2 * (para_CCS_captureCost + para_CCS_storageCost) + Emiss_CO2 * dccs_p * para_CCS_transCost
    OM_CCS = add_OM_CCS
    
    n = int(set_retrofitYr - operateYear_p) # because framework start from 0
    retro_lcoeframe = ori_lcoeFrame_p.copy()
    
    cost = np.sum(retro_lcoeframe[:n, 0:5])
    cost = cost + retro_lcoeframe[n,0] + (add_Cap_Flex * y_flex_p) + (add_Cap_BE * y_be_p) + (add_Cap_CCS * y_ccs_p)
    cost = cost + retro_lcoeframe[n,1] + (OM_BE * y_be_p) + (OM_CCS * y_ccs_p)
    
    leftYrs = 40 - n
    # r = 1.05
    # r = 1.08
    
    if n < lifespan:
        for i in range(n, lifespan):
            if i == n:
                # if it has been retrofitted before, the changes happen in the frame
                cost = cost + retro_lcoeframe[i, 0] + (add_Cap_Flex * y_flex_p) + (add_Cap_BE * y_be_p) + (add_Cap_CCS * y_ccs_p)
                cost = cost + retro_lcoeframe[i, 1] + (OM_BE * y_be_p) + (OM_CCS * y_ccs_p)
            elif i > n:
                cost = cost + ((OM_BE * y_be_p) + (OM_CCS * y_ccs_p))/pow(r, n+i+1) - retro_lcoeframe[i, 1] * y_retire_p
                cost = cost + fuel_coal + fuel_be - retro_lcoeframe[i, 2] * y_retire_p
    
    return cost
      

# from function.cal_cost_df import Initial_PP_lcoeDF
# y_flex_p = 1; y_be_p=0; y_ccs_p=0; y_retire_p = 0; cf_p = 0.5;
# # capacity_p = 300 * pow(10,3); hours_p = 5000; operateYear_p = 2000; set_retrofitYr = 2025
# # ori_lcoeFrame_p = Initial_PP_lcoeDF(capacity_p, hours_p, operateYear_p, set_retrofitYr, 'Value')
# # sum_j_xij_kwh = 200 * pow(10,3) * 5000; sum_j_DBxij = sum_j_xij_kwh * 1000; dccs_p = 200
# # columnName = 'Value'; reducedCO2 = 0; credit_perCO2 = 0

# cal_profit_credit(y_flex_p, y_be_p, y_ccs_p, y_retire_p, cf_p, ori_lcoeFrame_p, 
#                       capacity_p, hours_p, sum_j_xij_kwh,  sum_j_DBxij, dccs_p, 
#                       operateYear_p, set_retrofitYr, columnName, reducedCO2, credit_perCO2)/pow(10,8)
    