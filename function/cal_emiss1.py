# -*- coding: utf-8 -*-
"""
Created on Fri Jul  2 14:29:07 2021

@author: DELL
"""

import numpy as np
import pandas as pd

# y_flex[p], y_be[p], y_ccs[p], cf[p], capacity[p], hours[p], take.sum(p, '*'),  take.prod(distance, p, "*")
def cal_emiss(y_be_p_past, y_be_p, y_ccs_p_past, y_ccs_p, y_retire_p, cf_p, 
              capacity, hours, Sum_j_xij_kwh, Sum_j_DBxij, unitCoal):
    
    para_ef=pd.read_csv('function/params_emissFactor.csv',index_col='process')
    pp_emiss = cf_p * capacity * hours * para_ef.loc['coal_fireplant','value']
    be_offset = Sum_j_xij_kwh * para_ef.loc['coal_fireplant','value'] 
    beccs_absorb = Sum_j_xij_kwh * para_ef.loc['bio_absorb_rate','value']
    coalccs_capture = (cf_p * capacity * hours - Sum_j_xij_kwh) * para_ef.loc['coal_fireplant','value'] * para_ef.loc['ccs_rate','value']/pow(10,2)
    bio_LCA = Sum_j_xij_kwh * (para_ef.loc['bio_field_transfer','value'] + para_ef.loc['bio_pretreat1','value'] + para_ef.loc['bio_storage','value']+para_ef.loc['bio_pretreat2','value']) + Sum_j_DBxij * para_ef.loc['bio_road_transfer','value']
    coal_LCA = (cf_p * capacity * hours - Sum_j_xij_kwh) * (para_ef.loc['coal_mine','value'] + para_ef.loc['coal_trans','value'])
    # print('pp_emiss:%.1f; be_offset:-%.1f; beccs_absorb:-%.1f, coal_capture:-%.1f' % 
    #       (pp_emiss/scale_Bio, be_offset/scale_Bio, beccs_absorb/scale_Bio, coalccs_capture/scale_Bio))
    
    emiss = (pp_emiss  + bio_LCA *0 + coal_LCA*0) * (1-y_retire_p) - be_offset *(y_be_p_past + y_be_p) - beccs_absorb * (y_ccs_p_past + y_ccs_p) - coalccs_capture * (y_ccs_p_past + y_ccs_p)
    
    unit_gTton = pow(10,6)
    emiss_t = emiss/unit_gTton
    return emiss_t

def cal_emiss_yr(y_be_p_past, y_be_p, y_ccs_p_past, y_ccs_p, y_retire_p, cf_p, 
                 capacity, hours, Sum_j_xij_kwh, Sum_j_DBxij, unitCoal, inputYrs, currentYrs):
    
    para_ef=pd.read_csv('function/params_emissFactor.csv',index_col='process')
    pp_emiss = cf_p * capacity * hours * para_ef.loc['coal_fireplant','value']
    be_offset = Sum_j_xij_kwh * para_ef.loc['coal_fireplant','value'] 
    beccs_absorb = Sum_j_xij_kwh * para_ef.loc['bio_absorb_rate','value']
    coalccs_capture = (cf_p * capacity * hours - Sum_j_xij_kwh) * para_ef.loc['coal_fireplant','value'] * para_ef.loc['ccs_rate','value']/pow(10,2)
    bio_LCA = Sum_j_xij_kwh * (para_ef.loc['bio_field_transfer','value'] + para_ef.loc['bio_pretreat1','value'] + para_ef.loc['bio_storage','value']+para_ef.loc['bio_pretreat2','value']) + Sum_j_DBxij * para_ef.loc['bio_road_transfer','value']
    coal_LCA = (cf_p * capacity * hours - Sum_j_xij_kwh) * (para_ef.loc['coal_mine','value'] + para_ef.loc['coal_trans','value'])
    # print('pp_emiss:%.1f; be_offset:-%.1f; beccs_absorb:-%.1f, coal_capture:-%.1f' % 
    #       (pp_emiss/scale_Bio, be_offset/scale_Bio, beccs_absorb/scale_Bio, coalccs_capture/scale_Bio))
    
    emiss = (pp_emiss  + bio_LCA *0 + coal_LCA*0) * (1-y_retire_p) - be_offset * (y_be_p_past + y_be_p) - beccs_absorb * (y_ccs_p_past + y_ccs_p) - coalccs_capture * (y_ccs_p_past + y_ccs_p)
    
    unit_gTton = pow(10,6)
    emiss_t = emiss/unit_gTton
    
    if currentYrs - inputYrs > 40 or currentYrs < inputYrs:
        emiss_t = 0
        
    return emiss_t
    


# test
# y_be_p_past = 1; y_be_p = 0; y_ccs_p_past = 1; y_ccs_p=0; y_retire_p = 1
# cf=0.6
# capacity=500*pow(10,3)
# hours = 4000
# Sum_j_xij_kwh = 0
# Sum_j_DBxij = Sum_j_xij_kwh * 0
# unitCoal = 285
# cal_emiss(y_be_p_past, y_be_p, y_ccs_p_past, y_ccs_p, y_cr_p, cf, capacity, hours, Sum_j_xij_kwh, Sum_j_DBxij, unitCoal)
    
    
    
    
    
    
