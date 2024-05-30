# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 11:17:19 2024

@author: vicke
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from function.cal_emiss1 import cal_emiss
from function.cal_cost import cal_cost
from function.filter_ppDict import filter_pp, twoDict_to_oneDict
from function.cal_profit import update_lcoeframe
import time

def update_results(m, pp_dict1, take, y_flex, y_be, y_ccs, y_retire, cf, distance, set_retrofitYr, columnName):
    
    pp_dict_out = pp_dict1.copy()
    
    y_flex_dict = dict(m.getAttr('x', y_flex))
    y_be_dict = dict(m.getAttr('x', y_be))
    y_ccs_dict = dict(m.getAttr('x', y_ccs))
    y_retire_dict = dict(m.getAttr('x', y_retire))
    cf_dict = dict(m.getAttr('x', cf))
    take_dict = m.getAttr('x', take)
    
    for p in pp_dict1.keys():
        
        if y_flex_dict[p] == 1:
            pp_dict_out[p]['flex'] = (1, set_retrofitYr)
            pp_dict_out[p]['cf'] = cf_dict[p]
            print('%.f plant: flexible retorfit; capacity factor = %.3f' % (p, cf_dict[p]))
            
        if y_be_dict[p] == 1:
            pp_dict_out[p]['be'] = (1, set_retrofitYr)
            # print(time.time())
            pp_dict_out[p]['take'] = take_dict.sum(p, '*').getValue()
            pp_dict_out[p]['take_dis'] = take_dict.sum(distance, p, '*').getValue()
            # print(time.time())
            print('%.f plant: be retorfit; bioRes = %.3f kwh; take_dis = %.1f' % (p, pp_dict_out[p]['take'], pp_dict_out[p]['take_dis']))
        
        if y_ccs_dict[p] == 1:
            pp_dict_out[p]['ccs'] = (1, set_retrofitYr)
            print('%.f plant: ccs retorfit' % p)
            
        if y_retire_dict[p] == 1:
            pp_dict_out[p]['retire'] = (1, set_retrofitYr)
            pp_dict_out[p]['cf'] = cf_dict[p]
            print('%.f plant: retire' % p)
        
        # update lcoeframe
        if (y_flex_dict[p] + y_be_dict[p] + y_ccs_dict[p] + y_retire_dict[p]) >= 1:
            # print('update lcoeframe')
            # print(time.time())
            ori_lcoeFrame_p = pp_dict_out[p]['lcoe_df']
            lcoeframe, lcoe = update_lcoeframe(y_flex_dict[p], y_be_dict[p], y_ccs_dict[p], y_retire_dict[p], cf_dict[p], ori_lcoeFrame_p, 
                           pp_dict_out[p]['Capacity_kw'], pp_dict_out[p]['hours'], pp_dict_out[p]['take'],  
                           pp_dict_out[p]['take_dis'], pp_dict_out[p]['ccsDis_km'], pp_dict_out[p]['year'], 
                           set_retrofitYr, columnName)
            pp_dict_out[p]['lcoe_df'] = lcoeframe
            print('ori_lcoe:%.4f; retro_lcoe:%.4f' % (pp_dict_out[p]['C2020'], lcoe))
            # print(time.time())
    
    return pp_dict_out


def check_results(pp_dict_out, EMISS_GOAL, ELEC_GOAL, set_retrofitYr):
    
    #===== 1. check carbon emission target ======
    emiss_sum = 0.   
    # culculate emiss
    for p in pp_dict_out.keys():
        y_be_p = pp_dict_out[p]['be'][0]
        y_ccs_p = pp_dict_out[p]['ccs'][0]
        y_retire_p = pp_dict_out[p]['retire'][0]       
        cf_p = pp_dict_out[p]['cf']
        take = pp_dict_out[p]['take']
        take_dis = pp_dict_out[p]['take_dis']
        
        tmp_emiss = cal_emiss(0, y_be_p, 0, y_ccs_p, y_retire_p, cf_p, 
                    pp_dict_out[p]['Capacity_kw'], pp_dict_out[p]['hours'], 
                    take, take_dis, pp_dict_out[p]['CoalUnit_g/kwh'])
        
        pp_dict_out[p]['yrEmiss_10_6t'] = tmp_emiss / pow(10,6)
        demand = pp_dict_out[p]['Capacity_kw'] * pp_dict_out[p]['hours'] * cf_p
        pp_dict_out[p]['yrElec_10_9kwh'] =  demand / pow(10,9)
        
        if  demand < take:
            print('%.f plant take more %.f biomass more than coal plant %.f demand' % (p, take, demand))
        
        emiss_sum = emiss_sum + tmp_emiss
        if tmp_emiss <0:
            print('%.f: emiss: %.1f' % (p, tmp_emiss))
        # print('%.f: emiss: %.1f' % (p, tmp_emiss))
        
    if emiss_sum <= EMISS_GOAL:
        print('CO2 Constraint work: the total emission %.f <= %.f' % (emiss_sum, EMISS_GOAL))
    
    else:
        print('constraint violate: the total emission = %.f > %.f' % (emiss_sum, EMISS_GOAL))
    
    #====== 2. check electricity generation =======
    elec_sum = 0.
    for p in pp_dict_out.keys():
        elec_sum = elec_sum + pp_dict_out[p]['Capacity_kw'] * pp_dict_out[p]['hours'] * pp_dict_out[p]['cf']
        
    if elec_sum >= ELEC_GOAL:
        print('Elec Constraint work: newElec %.f >= %.f kwh' % (elec_sum, ELEC_GOAL))
        
    else:
        print('constraint violate: newElec %.f < %.f kwh' % (elec_sum, ELEC_GOAL))
    
    #====== 3. check total costs =========
    cost = 0.
    for p in pp_dict_out.keys():
        cost_tmp = cal_cost(pp_dict_out[p]['flex'][0], pp_dict_out[p]['be'][0], pp_dict_out[p]['ccs'][0],
                          pp_dict_out[p]['retire'][0], pp_dict_out[p]['cf'], pp_dict_out[p]['lcoe_df'],
                          pp_dict_out[p]['Capacity_kw'], pp_dict_out[p]['hours'], pp_dict_out[p]['take'],
                          pp_dict_out[p]['take_dis'], pp_dict_out[p]['ccsDis_km'],
                          pp_dict_out[p]['year'], set_retrofitYr, 'Value')     
        
        
        cost = cost + cost_tmp
        pp_dict_out[p]['totalCost_10_9dollar'] = cost_tmp / pow(10,9)
    
    print('total cost of all plants = %.1f billion dollars/year' % (cost / 40))
    return


def write_results(pp_dict_out, set_retrofitYr):    
    #======= 4. write results ===============
    # write pp_dict_out to excel
    tmp = pd.read_csv('input/pp_all.csv')
    pp_colName = list(tmp.columns)[1:]
    
    pp_csv_output = pd.DataFrame(columns=pp_colName) # select value according to the columns
    count = 0
    
    for p in pp_dict_out.keys():
        val_list = []
        for colName in pp_colName:
            tmp_val = pp_dict_out[p].get(colName)
            val_list.append(tmp_val)
        
        pp_csv_output.loc[count] = val_list
        count = count + 1
    
    pp_csv_output.to_csv('output/pp_all_' + str(set_retrofitYr) + '.csv')

    return pp_dict_out   

def write_results_loop(pp_dict_out, set_retrofitYr, path_id , pathName):    
    #======= 4. write results ===============
    # write pp_dict_out to excel
    tmp = pd.read_csv('input/pp_all.csv')
    pp_colName = list(tmp.columns)[1:]
    
    pp_csv_output = pd.DataFrame(columns = pp_colName)
    count = 0
    for p in pp_dict_out.keys():
        val_list = []
        for colName in pp_colName:
            # print(colName)
            tmp_val = pp_dict_out[p].get(colName)
            if colName == 'ID':
                val_list.append(p)
            else:
                tmp_val = pp_dict_out[p].get(colName)
                val_list.append(tmp_val)
                
        pp_csv_output.loc[count] = val_list
        count = count + 1
    
    pp_csv_output.to_csv('output/%s_%s_pp_all_%s.csv' % (str(path_id), pathName, str(set_retrofitYr)))
    
    return pp_dict_out


def visulize_results(set_retrofitYr):
    pp = pd.read_csv('output/pp_all_' + str(set_retrofitYr) + '.csv')
    
    # average operating hours
    ave_hours = np.sum(pp['hours'] * pp['cf'])/len(pp)
    print('the avarage operating hours: %.1f' % ave_hours)
    
    # technology choice share
    flex_pp = [int(x[1]) for x in pp.loc[:,'flex']]
    retire_pp = [int(x[1]) for x in pp.loc[:,'retire']]
    be_pp = [int(x[1]) for x in pp.loc[:,'be']]
    ccs_pp =[int(x[1]) for x in pp.loc[:,'ccs']]
    beAndccs_pp = pd.concat([pd.DataFrame(be_pp), pd.DataFrame(ccs_pp)], axis=1)
    beAndccs_pp.columns = ['be','ccs']
    beAndccs_pp['beccs'] = round((beAndccs_pp['be'] + beAndccs_pp['ccs'])/2)
    
    retireNum = np.sum(retire_pp); flexNum = np.sum(flex_pp); beccsNum = np.sum(beAndccs_pp['beccs'])
    beNum = np.sum(beAndccs_pp['be']) - beccsNum
    ccsNum = np.sum(beAndccs_pp['ccs']) - beccsNum
    ppNum = len(pp) - retireNum - beccsNum - beNum - ccsNum
    
    num_label = ['be','ccs','beccs','retire', 'pp']
    data = [beNum, ccsNum, beccsNum, retireNum, ppNum]
    print('plant number: be: %.1f; ccs:%.1f; beccs:%.1f; retire: %.1f; pp:%.1f; flex: %.1f' % 
          (beNum, ccsNum, beccsNum, retireNum, ppNum, flexNum))    
    # plt.pie(data, labels = num_label)
    
    return

def update_bioDict(bio_dict, take, dict_power2res):
    update_bio_dict = bio_dict.copy() # biomass dict that need to be updated
    
    list_power2res_key = list(dict_power2res.keys())
    bio_key = set([x[1] for x in list_power2res_key]) # unique bio key
    
    for bio_id in bio_key:
        betaken = take.sum('*', bio_id).getValue()
        if betaken > 0:
            tmp_val = bio_dict.get(bio_id)
            left_bioValue = tmp_val[0] - betaken
            tmp_val1 = [left_bioValue, tmp_val[1]]
            update_bio_dict[bio_id] = tmp_val1
            
    return update_bio_dict
    
    

    
    
    
    
    
    
    
    
    