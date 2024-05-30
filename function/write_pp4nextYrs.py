# -*- coding: utf-8 -*-
"""
Created on Sat Apr  6 10:14:11 2024

@author: vicke
"""

import numpy as np
import pandas as pd
import pickle

def write_PPs_4nextYrs_pkl(pp_dict_out1, set_retrofitYr):
    
    # open the original pp file
    oldYr = int(set_retrofitYr - 5)
    with open('input/CoalPlants/powerplants_%s.pkl'%str(oldYr), 'rb') as f:
        ori_pp_dict = pickle.load(f)
        
    # update the last information of the coal plants
    for p in pp_dict_out1.keys():
        ori_pp_dict[p] = pp_dict_out1[p]
    
    # update this yrs pp plants
    with open('input/CoalPlants/powerplants_%s.pkl' % str(set_retrofitYr), 'wb') as f:
        pickle.dump(ori_pp_dict, f) # save the filter results
    
    # write the results to output file
    with open('output/pp_%s.pkl' % str(set_retrofitYr), 'wb') as f:
        pickle.dump(ori_pp_dict, f)        
        
    
def write_PPs_4nextYrs_pkl_loop(pp_dict_out1, set_retrofitYr, path_id , pathName):
    
    # open the original pp file
    with open('input/CoalPlants/powerplants_2020.pkl', 'rb') as f:
        ori_pp_dict = pickle.load(f)

    for p in pp_dict_out1.keys():
        ori_pp_dict[p] = pp_dict_out1[p]
    
    # update this yrs pp plants
    with open('input/CoalPlants/powerplants_%s.pkl' % str(set_retrofitYr), 'wb') as f:
        pickle.dump(ori_pp_dict, f) # save the filter results
    
    # write the results to output file
    with open('output/%s_%s_pp_all_%s.csv' % (str(path_id), pathName, str(set_retrofitYr)), 'wb') as f:
        pickle.dump(ori_pp_dict, f)
        