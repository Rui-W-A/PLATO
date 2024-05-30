# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 15:55:26 2023

@author: vicke
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# import function.cal_emiss as cal_emiss
from function.cal_emiss1 import cal_emiss_yr
import random
import math

# cal_emiss_yr(y_be_p_past, y_be_p, y_ccs_p_past, y_ccs_p, y_retire_p, cf_p, 
#         capacity, hours, Sum_j_xij_kwh, Sum_j_DBxij, unitCoal, inputYrs, currentYrs)
# pp = pd.read_csv('input/pp_all.csv')

# emission from 2020 to 2060
# emiss = dict()
# for year in range(2020,2065,5):  # from 2020 to 2065
#     pp['E'+str(year)] = pp.apply(lambda x: cal_emiss_yr(int(x['be'][1]), 0,int(x['ccs'][1]), 0,
#         0, x['cf'], x['Capacity_kw'], x['hours'],0,0,x['CoalUnit_g/kwh'], x['year'], year), axis=1)
#     emiss_y = pp['E'+str(year)].sum()
#     emiss.update({year:emiss_y})
# cluster_path = dict()
# pathdict = dict()
# peakYr = 2040
# zeroYr = 2060
# CuER_target = 0.3
# randNum = 1000
# rd = np.random.RandomState(888) # guarantee the same random number;
# flucMatrix = rd.uniform(0,1, (8,100)) # rowNum = yr; colNum = times;

# pp = pd.DataFrame
# emiss = dict()
# cluster_path = dict()
pathdict = dict()
# peakYr, peakYr, CuER_target, randNum = 0,0,0,0
# rd = np.random.RandomState(888) # guarantee the same random number;
# flucMatrix = rd.uniform(0,1, (8,100)) # rowNum = yr; colNum = times;


def draw_curve(emiss, preYrEmiss, currentYr, peakYr, zeroYr, flucMatrix, j):
    tmp = 0.
    if currentYr <= peakYr and currentYr < 2050:
        i = int((currentYr - 2025)/5)
        if emiss[currentYr] > preYrEmiss:
            print(currentYr)
            tmp = preYrEmiss + flucMatrix[i,j] * (emiss[currentYr] - preYrEmiss)
            pathdict.update({currentYr: tmp})
            preYrEmiss = tmp.copy()
            currentYr = currentYr + 5
            return draw_curve(emiss, preYrEmiss, currentYr, peakYr, zeroYr, flucMatrix, j)
        else:
            return 
        
    elif currentYr == zeroYr:
        print(currentYr)
        # tmp = 0
        pathdict.update({currentYr: 0})
        # preYrEmiss = 0
        currentYr = currentYr + 5
        return    
    
    elif currentYr > peakYr and currentYr <= 2050:
        print(currentYr)
        i = int((currentYr - 2025)/5)
        tmp = min(emiss[currentYr], preYrEmiss) * (1-flucMatrix[i,j])
        pathdict.update({currentYr: tmp})
        preYrEmiss = tmp.copy()
        currentYr = currentYr + 5
        return draw_curve(emiss, preYrEmiss, currentYr, peakYr, zeroYr, flucMatrix, j)

    elif currentYr >= 2050:
        return
        # i = int((currentYr - 2025)/5)
        # tmp = min(emiss[currentYr], preYrEmiss) * (1-flucMatrix[i,j])
        # pathdict.update({currentYr: tmp})
        # print(currentYr)
        # return tmp

def gen_CERPs_CuER(peakYr, zeroYr, CuER_target, randNum):
    
    # global cluster_path, pathdict, peakYr, zeroYr, CuER_target, rd, flucMatrix, emiss, pp
    pp = pd.read_csv('input/pp_all.csv')
    emiss = dict()
    for year in range(2020,2055,5):  # from 2020 to 
        pp['E'+str(year)] = pp.apply(lambda x: cal_emiss_yr(int(x['be'][1]), 0,int(x['ccs'][1]), 0,
                     0, x['cf'], x['Capacity_kw'], x['hours'],0,0,x['CoalUnit_g/kwh'], x['year'], year), axis=1)
        
        emiss_y = pp['E'+str(year)].sum()
        emiss.update({year: emiss_y})
    
    print('peak year: %.1f; zero year: %.1f; CuER target: %.1f; randNum: %.1f' %  (peakYr, zeroYr, CuER_target, randNum))
    
    rd = np.random.RandomState(888) # guarantee the same random number
    flucMatrix = rd.uniform(0,1, (6,randNum)) # rowNum = yr; colNum = times;
    
    cluster_path = dict()
    for j in range(flucMatrix.shape[1]):
        global pathdict
        pathdict = dict()
        preYrEmiss = emiss[2020] # update the first year
        pathdict.update({2020: preYrEmiss})
        currentYr = 2025
        draw_curve(emiss, preYrEmiss, currentYr, peakYr, zeroYr, flucMatrix, j)    
        if len(pathdict) < (2055-2020)/5:
            print(j)
            continue
        cluster_path.update({j: pathdict})
    
    # filter and plot the given CuER line
    CuER_CERP = dict()
    yr_list = list(emiss.keys())
    emiss_list = list(emiss.values())
    
    fig, ax = plt.subplots()
    ax.plot(yr_list, emiss_list)
    for j in cluster_path.keys():
        CERP_list = list(cluster_path[j].values())
        CuER_tmp = (sum(emiss_list) - sum(CERP_list)) / sum(emiss_list)
        ax.plot(yr_list, CERP_list, c='b', alpha=0.2, linestyle='--')
        
        if abs(CuER_tmp - CuER_target) <= 0.02:
            ax.plot(yr_list, CERP_list, c='r')
            CuER_CERP.update({j: CERP_list})

    ori_CERP = pd.DataFrame(emiss_list)
    ori_CERP.index = yr_list
    ori_CERP.columns = ['ori_Emiss_t']
    df_CuER_CERPs = pd.DataFrame.from_dict(CuER_CERP)
    df_CuER_CERPs.index = yr_list
    out_CERPs = pd.concat([ori_CERP, df_CuER_CERPs], axis = 1)
    fileName = 'CuER_' + str(int(CuER_target * 100)) + 'per' + '_' + str(peakYr) + 'p' + '_' + str(zeroYr) + 'zero'
    out_CERPs.to_excel('input/CuER_CERPs/' + fileName + '.xlsx')
    print('total number of pathways: %.1f' % out_CERPs.shape[1])
    
    return out_CERPs