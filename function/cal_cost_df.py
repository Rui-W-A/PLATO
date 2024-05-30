# -*- coding: utf-8 -*-
"""
Created on Sun Mar 10 19:06:26 2024

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
para_be_capital = para.loc['BE-capital', 'Value'] 
para_be_fixOM = para.loc['BE-fixOM', 'Value']
para_be_variOM = para.loc['BE-variableOM', 'Value'] 
para_be_purchaseCost = para.loc['BE-purchaseCost', 'Value'] 
para_be_pretreatCost = para.loc['BE-pretreatCost', 'Value'] 
para_be_trans1 = para.loc['BE-transportCost1', 'Value']
para_be_trans2 = para.loc['BE-transportCost2', 'Value']
para_CCS_capital = para.loc['CCS-capital', 'Value'] 
para_CCS_captureCost = para.loc['CCS-captureCost', 'Value'] 
para_CCS_transCost = para.loc['CCS-transportCost', 'Value'] 
para_CCS_storageCost = para.loc['CCS-storageCost', 'Value'] 
r = 1.05
# r = 1.03
# r = 1.08
lifespan = 40
scale_Bio = pow(10,9)

def updateParas(columnName):
    # Parameters
    para = pd.read_csv('function/params_economic.csv', encoding = 'gbk')
    para = para.set_index('Parameter')
    para_be_capital = para.loc['BE-capital', columnName] # 变化    
    para_be_purchaseCost = para.loc['BE-purchaseCost', columnName] # 变动    
    para_be_pretreatCost = para.loc['BE-pretreatCost', columnName] # 变动    
    para_CCS_capital = para.loc['CCS-capital', columnName] # 变动    
    para_CCS_captureCost = para.loc['CCS-captureCost', columnName] # 变动
    para_CCS_transCost = para.loc['CCS-transportCost', columnName] # 变动    
    para_CCS_storageCost = para.loc['CCS-storageCost', columnName] # 变动
    return [para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, 
            para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost]


def Cal_lcoe_fromDF(LCOEframe):
    lcoe = np.sum(LCOEframe[:, 0:5])/np.sum(LCOEframe[:, 5])
    return lcoe

def Initial_PP_lcoeDF(capacity, hours, inputYrs, currentYrs, columnName):
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
    
    Cap_PP = para_pp_capital * capacity # CAPEX = 3274 $/kw
    OM_PP = (para_pp_fixOM + para_pp_variOM) * capacity
    Fuel_PP = capacity * hours * para_pp_coalCost / pow(10,3)
    Debt_PP = Cap_PP * 0.0
    D_PP = 0.05 * Cap_PP
    columnName = ['Equip','OM','Fuel','Debt','D','Elec']
    
    LCOEframe = np.zeros(shape=(lifespan, 6))
    elec = capacity * hours
    
    for i in range(lifespan):
        if i == 0:
            LCOEframe[i] = np.divide([Cap_PP, OM_PP, Fuel_PP, Debt_PP, 0. , elec], pow(r, i + 1))
        if i < 10 and i > 0:
            LCOEframe[i] = np.divide([0., OM_PP, Fuel_PP, Debt_PP, 0. , elec], pow(r, i + 1))
        if i == lifespan - 1:
            LCOEframe[i] = np.divide([0., OM_PP, Fuel_PP, 0. , -D_PP , elec], pow(r, i + 1))
        if i >= 10 and i < lifespan - 1:
            LCOEframe[i] = np.divide([0., OM_PP, Fuel_PP, 0. , 0. , elec], pow(r, i + 1))
    
    return LCOEframe
    
def Initial_CCS_lcoeDF(capacity, hours, disCCS, inputYrs, currentYrs, columnName, unitCoal):
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
    Emiss_CO2 = (275.1 + 14.8) * capacity * hours / pow(10,6) + unitCoal* 2.7725 * capacity * hours /pow(10,6) # unit: tonne
    
    Cap_CCS = (para_pp_capital + para_CCS_capital) * capacity
    OM_PP = (para_pp_fixOM + para_pp_variOM) * capacity
    OM_CCS = Emiss_CO2 * (para_CCS_captureCost + para_CCS_storageCost) + Emiss_CO2 * disCCS * para_CCS_transCost
    OM_PPCCS = OM_PP + OM_CCS
    Debt_CCS = 0.0 * Cap_CCS
    D_CCS = 0.05 * Cap_CCS
    Fuel_CCS = capacity * hours * para_pp_coalCost / pow(10,3)
    
    elec = capacity * hours
    LCOEframe = np.zeros(shape=(lifespan, 6))
    
    for i in range(lifespan):
        if i == 0:
            LCOEframe[i] = np.divide([Cap_CCS, OM_PPCCS, Fuel_CCS, Debt_CCS, 0. , elec], pow(r, i + 1))
        if i < 10 and i > 0:
            LCOEframe[i] = np.divide([0., OM_PPCCS, Fuel_CCS, Debt_CCS, 0. , elec], pow(r, i + 1))
        if i == lifespan - 1:
            LCOEframe[i] = np.divide([0., OM_PPCCS, Fuel_CCS, 0. , -D_CCS , elec], pow(r, i + 1))
        if i >= 10 and i < lifespan - 1:
            LCOEframe[i] = np.divide([0., OM_PPCCS, Fuel_CCS, 0. , 0. , elec], pow(r, i + 1))
    
    return LCOEframe
    
# def Add_BE_first_DF(LCOEframe, capacity, hours, sum_j_xij_kwh, sum_j_dbxij, inputYrs, retrofitYrs, columnName):
#      para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
     
#      add_Cap_BE = para_be_capital * capacity
#      add_OM_BE = (para_be_fixOM + para_be_variOM) * capacity
#      Fuel_BE = (para_be_purchaseCost + para_be_pretreatCost + para_be_trans2) * capacity * hours/pow(10,3) * scale_Bio
#      Fuel_PP = capacity * hours * para_pp_coalCost / pow(10,3) # coal price = 11.45/MWh
#      Fuel_BE_PPpart = capacity * hours * para_pp_coalCost/pow(10,3) - sum_j_xij_kwh * para_pp_coalCost / pow(10,3) * scale_Bio
#      add_Fuel = Fuel_BE_PPpart + Fuel_BE - Fuel_PP  # coal reduction cost and biomass cost
     
#      add_Debt_BE = add_Cap_BE * 0.0
#      add_D_BE = add_Cap_BE * 0.05
     
#      n = int(retrofitYrs - inputYrs + 1)
#      retro_lcoeframe = LCOEframe.copy()
     
#      if n < lifespan:
#          for i in range(n, lifespan):
#              if i == n: # the first year to retrofit
#                  retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([add_Cap_BE, add_OM_BE, add_Fuel, 0., 0., 0.], pow(r, i+1))
#              if i < (n+10) and i > n:
#                  retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([0., add_OM_BE, add_Fuel, add_Debt_BE, 0., 0.], pow(r, i+1))
#              if i >= (n+10) and i < lifespan - 1:
#                  retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([0., add_OM_BE, add_Fuel, 0., 0., 0.,], pow(r, i+1))
#              if i == lifespan - 1:
#                  retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([0., add_OM_BE, add_Fuel, 0., -add_D_BE, 0.], pow(r, i+1))
     
#      return retro_lcoeframe

# def Add_BE_after_DF(LCOEframe, capacity, hours, sum_j_xij_kwh, sum_j_dbxij, inputYrs, retrofitYrs):
#     n = retrofitYrs - inputYrs + 1
    
#     Fuel_BE = (para_be_purchaseCost + para_be_pretreatCost + para_be_trans2) * capacity * hours/pow(10,3) * scale_Bio
#     Fuel_BE_PPpart = capacity * hours * para_pp_coalCost/pow(10,3) - sum_j_xij_kwh * para_pp_coalCost / pow(10,3) * scale_Bio
#     fuel_cost = Fuel_BE + Fuel_BE_PPpart
    
#     retro_lcoeframe = LCOEframe.copy()
#     if n < lifespan:
#         for i in range(n, lifespan):
#             retro_lcoeframe[i][2] = fuel_cost/pow(r, i+1)
    
#     return retro_lcoeframe            


# def Add_flexi_first_DF(LCOEframe, capacity, hours, inputYrs, retrofitYrs, columnName, newHours):
#     red_hours = hours - newHours
#     add_Cap_Flexi = para_pp_capital * 0.1
#     add_OM_Flexi = (para_pp_fixOM + para_pp_variOM) * 0.1    
    
#     n = retrofitYrs - inputYrs + 1
#     retro_lcoeframe = LCOEframe.copy()
    
#     if n < lifespan:
#         for i in range(n, lifespan):
#             if i == n: # the first year to retrofit
#                 retro_lcoeframe[i] = retro_lcoeframe[i] * np.divide([add_Cap_Flexi, add_OM_Flexi, 0., 0, 0., -red_hours], pow(r, i+1))
#             if i > n:
#                 retro_lcoeframe[i] = retro_lcoeframe[i] * np.divide([0., 0., 0., 0, 0., -red_hours], pow(r, i+1))
    
#     return retro_lcoeframe    

# def Add_flexi_after_DF(LCOEframe, capacity, hours, inputYrs, retrofitYrs, newHours):
#     n = retrofitYrs - inputYrs + 1
#     retro_lcoeframe = LCOEframe.copy()
    
#     newElec = newHours * capacity
    
#     if n < lifespan:
#         for i in range(n, lifespan):
#             retro_lcoeframe[i][5] = newElec/pow(r,i+1)
    
#     return retro_lcoeframe
 
     
# def Add_CCS_DF(LCOEframe, capacity, hours, dccs, inputYrs, retrofitYrs, columnName):
#     para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
    
#     add_Cap_CCS = para_CCS_capital * capacity
#     Emiss_CO2 = capacity * hours * 0.801 / pow(10,3)
#     add_OM_CCS = Emiss_CO2 * (para_CCS_captureCost + para_CCS_storageCost) + Emiss_CO2 * dccs * para_CCS_transCost
#     add_Debt_CCS = 0.0 * add_Cap_CCS
#     add_D_CCS = 0.05 * add_Cap_CCS
#     add_Fuel_CCS = 0.
    
#     n = retrofitYrs - inputYrs + 1
#     retro_lcoeframe = LCOEframe.copy()
    
#     if n < lifespan:
#         for i in range(n, lifespan):
#             if i == n:
#                 retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([add_Cap_CCS, add_OM_CCS, add_Fuel_CCS, 0., 0., 0.], pow(r, i+1))
            
#             if i < (n+10) and i > n:
#                 retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([0., add_OM_CCS, add_Fuel_CCS, add_Debt_CCS, 0., 0.], pow(r, i+1))
            
#             if i >= (n+10) and i < lifespan - 1:
#                 retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([0., add_OM_CCS, add_Fuel_CCS, 0., 0., 0.], pow(r, i+1))
            
#             if i == lifespan - 1:
#                 retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([0., add_OM_CCS, add_Fuel_CCS, 0., -add_D_CCS, 0.], pow(r, i+1))
    
#     return retro_lcoeframe

# def Add_BECCS_first_DF(LCOEframe, capacity, hours, sum_j_xij_kwh, sum_j_dbxij, dccs, inputYrs, retrofitYrs, columnName):
#     para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
    
#     add_Cap_BE = para_be_capital * capacity
#     add_OM_BE = (para_be_fixOM + para_be_variOM) * capacity
#     Fuel_BE = (para_be_purchaseCost + para_be_pretreatCost + para_be_trans2) * capacity * hours/pow(10,3) * scale_Bio
#     Fuel_PP = capacity * hours * para_pp_coalCost / pow(10,3) # coal price = 11.45/MWh
#     Fuel_BE_PPpart = capacity * hours * para_pp_coalCost/pow(10,3) - sum_j_xij_kwh * para_pp_coalCost / pow(10,3) * scale_Bio
#     add_Fuel = Fuel_BE_PPpart + Fuel_BE - Fuel_PP  # coal reduction cost and biomass cost
#     add_Debt_BE = add_Cap_BE * 0.0
#     add_D_BE = add_Cap_BE * 0.05
    
#     add_Cap_CCS = para_CCS_capital * capacity
#     Emiss_CO2 = capacity * hours * 0.801 / pow(10,3)
#     add_OM_CCS = Emiss_CO2 * (para_CCS_captureCost + para_CCS_storageCost) + Emiss_CO2 * dccs * para_CCS_transCost
#     add_Debt_CCS = 0.0 * add_Cap_CCS
#     add_D_CCS = 0.05 * add_Cap_CCS
#     add_Fuel_CCS = 0.
    
#     add_Cap_BECCS = add_Cap_BE + add_Cap_CCS
#     add_OM_BECCS = add_OM_BE + add_OM_CCS
#     add_Debt_BECCS = add_Debt_BE + add_Debt_CCS
#     add_D_BECCS = add_D_BE + add_D_CCS
#     add_Fuel_BECCS = add_Fuel + add_Fuel_CCS
    
#     n = retrofitYrs - inputYrs + 1
#     retro_lcoeframe = LCOEframe.copy()
    
#     if n < lifespan:
#         for i in range(n, lifespan):
#             if i == n:
#                 retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([add_Cap_BECCS, add_OM_BECCS, add_Fuel_BECCS, 0., 0., 0.], pow(r, i+1))
            
#             if i < (n+10) and i > n:
#                 retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([0., add_OM_BECCS, add_Fuel_BECCS, add_Debt_BECCS, 0., 0.], pow(r, i+1))
            
#             if i >= (n+10) and i < lifespan - 1:
#                 retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([0., add_OM_BECCS, add_Fuel_BECCS, 0., 0., 0.], pow(r, i+1))
            
#             if i == lifespan - 1:
#                 retro_lcoeframe[i] = retro_lcoeframe[i] + np.divide([0., add_OM_BECCS, add_Fuel_BECCS, 0., -add_D_BECCS, 0.], pow(r, i+1))
    
#     return retro_lcoeframe

# def Add_BECCS_after_DF(LCOEframe, capacity, hours, sum_j_xij_kwh, sum_j_dbxij, inputYrs, retrofitYrs):
#     n = retrofitYrs - inputYrs + 1
    
#     Fuel_BE = (para_be_purchaseCost + para_be_pretreatCost + para_be_trans2) * capacity * hours/pow(10,3) * scale_Bio
#     Fuel_BE_PPpart = capacity * hours * para_pp_coalCost/pow(10,3) - sum_j_xij_kwh * para_pp_coalCost / pow(10,3) * scale_Bio
#     fuel_cost = Fuel_BE + Fuel_BE_PPpart
    
#     retro_lcoeframe = LCOEframe.copy()
#     if n < lifespan:
#         for i in range(n, lifespan):
#             retro_lcoeframe[i][2] = fuel_cost/pow(r, i+1)
    
#     return retro_lcoeframe    


# def Add_Retire_DF(LCOEframe, inputYrs, retrofitYrs):
    
#     n = retrofitYrs - inputYrs + 1
#     retro_lcoeframe = LCOEframe.copy()
    
#     add_D = np.sum(LCOEframe[:n, 0:1]) * 0.05 / pow(r, n+1)
    
#     if n < lifespan:
#         for i in range(n, lifespan):
#             retro_lcoeframe[i] = retro_lcoeframe[i] * [0., 0., 0., 0, 0., 0.]
        
#         retro_lcoeframe[n] = retro_lcoeframe[n] + [0., 0., 0., 0., -add_D, 0.]
    
#     return retro_lcoeframe



    
    
    
    
    
    
    
    