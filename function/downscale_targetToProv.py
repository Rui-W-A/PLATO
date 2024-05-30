# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 11:32:19 2024

@author: vicke
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from function.cal_emiss1 import cal_emiss_yr

def downscale_targetToProv(emiss_path):
    pp = pd.read_csv('input/pp_all.csv')
    prov_name_arr = pp['prov'].unique()
    
    # === 0. prepare some empty dataframe =======
    zero_arr = np.zeros((len(prov_name_arr), 7))
    prov_df_emiss = pd.DataFrame(zero_arr, index=prov_name_arr, columns=[x for x in range(2020,2055,5)])
    prov_df_elec = prov_df_emiss.copy()
    df_prov_emissTarget = prov_df_emiss.copy()
    
    # === 1. calculate BUA emission pathway for each province =======
    for prov_name in prov_name_arr:
        pp_prov_tmp = pp[pp['prov'] == prov_name]
        for year in range(2020, 2055, 5):
            pp_prov_tmp['E'+str(year)] = pp_prov_tmp.apply(lambda x: cal_emiss_yr(int(x['be'][1]), 0,int(x['ccs'][1]), 0,
                         0, x['cf'], x['Capacity_kw'], x['hours'],0,0,x['CoalUnit_g/kwh'], x['year'], year), axis=1)

            # pp_prov_tmp.loc[:,'E'+str(year)] = np.where((pp_prov_tmp['year'] + 40 > year)&(pp_prov_tmp['year'] < year), pp_prov_tmp['E2020'], 0)
            pp_prov_tmp.loc[:,'Elec'+str(year)] = np.where((pp_prov_tmp['year'] + 40 > year)&(pp_prov_tmp['year'] < year), pp_prov_tmp['Capacity_kw'] * pp_prov_tmp['hours'], 0)
            emiss_prov_sum = pp_prov_tmp['E'+str(year)].sum()
            elec_prov_sum = pp_prov_tmp['Elec'+str(year)].sum()
            # update the value to the df
            prov_df_emiss.loc[prov_name, year] = emiss_prov_sum
            prov_df_elec.loc[prov_name, year] = elec_prov_sum
    
    # === 2. downscale the emiss pathway based on the share of original emission in that year ======
    for year in range(2020, 2055, 5):
        # emission target for each province = national target / ori emission in that province in that year
        prov_share_yr = prov_df_emiss.loc[:, year] / prov_df_emiss.loc[:, year].sum()
        df_prov_emissTarget.loc[:, year] = emiss_path[year] * prov_share_yr
        
    # === 3. compare the downscaling results with the BUA emission pathway
    diff_BAU_CN = prov_df_emiss - df_prov_emissTarget
    
    # === 4. plot emission pathway ========
    plt.plot(df_prov_emissTarget.T)
    
    return df_prov_emissTarget, prov_df_elec