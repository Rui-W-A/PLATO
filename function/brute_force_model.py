# -*- coding: utf-8 -*-
"""
Created on Fri Apr 19 12:40:08 2024

@author: vicke
"""

import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB

def brute_force_model(pp_dict1, set_retrofitYr, ELEC_GOAL):
    
    force_retire_ppdict = dict()
    tryagain_ppdict = dict()
    
    # cap_index = pd.DataFrame(columns=['Capacity','hours','keyID'])
    cap_list = []
    elec_sum = 0.

    # first divide the dict    
    for key_id in pp_dict1.keys():
        
        opt_be = pp_dict1[key_id]['be'][0]
        opt_ccs = pp_dict1[key_id]['ccs'][0]
        opt_flex = pp_dict1[key_id]['flex'][0]
        
        if opt_be == 0 | opt_ccs == 0:
            tmp = pp_dict1[key_id]
            # print(key_id)
            tmp['retire'] = (1, set_retrofitYr)
            force_retire_ppdict.update({key_id: tmp})
            cap_list.append([tmp['Capacity_kw'], tmp['hours'], tmp['keyID']])
        
        else:
            # print(key_id)
            tmp = pp_dict1[key_id]
            elec_sum = elec_sum + tmp['Capacity_kw'] * tmp['hours']
            tryagain_ppdict.update({key_id: tmp}) 
            
    # check whether the electricity can meet the target
    if elec_sum < ELEC_GOAL:
        cap_df = pd.DataFrame(cap_list, columns=['Capacity','hours','keyID'])
        cap_df['elec'] = cap_df['Capacity'] * cap_df['hours']
        cap_df=cap_df.sort_values('elec', ascending=False)
        cap_df.index = cap_df['keyID']
        
        key_id_record = []
        for key_id in cap_df.index:
            tmp_elec = cap_df.loc[key_id, 'elec']
            elec_sum = elec_sum + tmp_elec
            if elec_sum + tmp_elec > ELEC_GOAL:
                key_id_record.append(key_id)
                break
        
        # delete the value in force_retire_ppdict; add the record in tryagain_dict
        for trans_id in key_id_record:
            tryagain_ppdict.update({trans_id: force_retire_ppdict[trans_id]})
            del force_retire_ppdict[trans_id]
    
    print("%.f coal plant will rejoin the model" % (len(tryagain_ppdict)))
    
    return tryagain_ppdict, force_retire_ppdict


def shut_down(pp_dict1, set_retrofitYr):
    pp_dict_out = pp_dict1.copy()
    for key_id in pp_dict1.keys():
        pp_dict_out[key_id]['retire'] = (1, set_retrofitYr)
    
    return pp_dict_out
     