# -*- coding: utf-8 -*-
"""
Created on Tue Sep 27 15:11:59 2022

@author: vicke
"""

import gurobipy as gp
from gurobipy import GRB
import pickle
import pandas as pd
import numpy as np
from function.pretreat_coalPlant_China import pretreat_coalPlant_China
from function.generate_coalPathway import gen_CERPs_CuER 
from function.generate_bioDict import generate_bioDict
from function.filter_ppDict import filter_pp, twoDict_to_oneDict
from function.generate_disDict import generate_disDict
from function.build_model import build_model
import time
from function.post_process import check_results, visulize_results, write_results, update_results, update_bioDict
from function.write_pp4nextYrs import write_PPs_4nextYrs_pkl
from function.downscale_targetToProv import downscale_targetToProv
import sys
import matplotlib.pyplot as plt
from function.brute_force_model import brute_force_model, shut_down

# module 1. prepare coal power plants
# pretreat_coalPlant_China()
# tmp = pd.read_csv('input/pp_all.csv')
# bio_data = np.load('input/RawData/res_kwh_20km_AF.npy')
# fig, ax = plt.subplots()
# ax.imshow(bio_data)
# ax.scatter(tmp['pixelX'], tmp['pixelY'])

# module 2. generate emissions scenario
# peakYr = 2030 # 2025
# zeroYr = 2060 # 2060
# CuER_target = 0.3
# randNum = 5000
# df_CERPs = gen_CERPs_CuER(peakYr, zeroYr, CuER_target, randNum)
# emiss_path = df_CERPs.iloc[:, 1]
# ori_emiss_path = df_CERPs.iloc[:, 0]

df_CERPs = pd.read_excel('input/CuER_CERPs/CERPs_50per.xlsx', index_col=0)
number = 8
emiss_path = df_CERPs.iloc[:, number]
print("path number: %f" % number)
ori_emiss_path = df_CERPs.iloc[:, 0]

# module 3. coal electricity load constraints
coalElec_base = pd.read_excel('input/Exogenous_Constraints/coalElec_baseload_prov.xlsx', index_col='CoalElec_kWh')
emissTarget_prov, prov_df_elec = downscale_targetToProv(emiss_path)
coalElec_base1 = coalElec_base.copy()
emissTarget_prov.to_excel('output/province_CO2target.xlsx')

for prov in prov_df_elec.index:
    nc_kwh = np.array(coalElec_base.loc[prov, 2025:])
    plant_kwh = np.array(prov_df_elec.loc[prov, 2025:])
    coalElec_base1.loc[prov,:] = np.minimum(nc_kwh, plant_kwh)

elecPrice = 0.06 # 0.048 - 0.072

# module 4. solve model: 
# (1) first solve the national prov-by-prov
# (2) second iterate by year
sys.stdout = open('log.txt','w')

start0 = time.time()
for year in range(2025, 2055, 5):
    # time calculation
    start = time.time()
    
    # ps: solve the province with the maximum carbon emission amount
    prov_target_yr = emissTarget_prov.sort_values(year, ascending=False)[year]
    set_retrofitYr = year
    
    # 4.1 read biomass resource; the occupied biomass resource need to be deducted
    bio_filePath = 'input/RawData/res_kwh_20km_AF.npy'
    bio_dict = generate_bioDict(bio_filePath)  # kwh
    
    # 4.2 out_pp_dict will be update after the calculation for all provinces
    out_allProvPP_dict = dict()
    
    for prov_name in prov_target_yr.index:
        print('province: %s' % prov_name)
        # 4.2 read the goal for this province
        EMISS_GOAL = emissTarget_prov.loc[prov_name, year]
        
        # 4.3 read the base load of electricity; unit: kwh
        ELEC_GOAL = coalElec_base1.loc[prov_name, year]
        
        # 4.4 read last year's plant
        oldYear = set_retrofitYr - 5
        pp_dict = dict()
        with open('input/CoalPlants/powerplants_'+ str(int(oldYear)) +'.pkl', 'rb') as f:
            pp_dict = pickle.load(f) # contains all coal plants' information
            
        # filter plants by province, and also consider its' choice and lifespan
        pp_dict_prov = {key: pp_dict[key] for key in pp_dict.keys() if pp_dict[key]['prov'] == prov_name}
        pp_dict1 = filter_pp(pp_dict_prov, set_retrofitYr) 
        
        if len(pp_dict1) == 0:
            print('the pp in %s province in %.f year are all retired' % (prov_name, year))
            continue
        
        # 4.4 begin the optimization
        radius_limit = 20  # distance = radius_limit * 10km
        # if year >= 2045:
        #     radius_limit = 50
        gap_set = 0.01   # 5%
        resolution = 20
        mode = 'All'
        columnName = 'Value'
        
        # convert the dict in the dict as one dict, the other dict use dataframe to store
        tmp_ppDict = twoDict_to_oneDict(pp_dict1) 
        
        # varaibles for gurobi
        power_station_id, keyID, PPs_hours, InsCapacity, unitCoal, lon, lat, operateYear, pixelX, pixelY, dccs, y_opt, take, cost, emiss, pp_pos, ori_lcoeFrame, retrofitYear, flex, be, ccs, retire = gp.multidict(tmp_ppDict)
        
        # variable for biomass
        res_point_id, resources, res_loc = gp.multidict(bio_dict)
        
        # distance matrix
        dict_power2res = generate_disDict(pp_pos, res_loc, radius_limit, resolution)
        power2res, distance = gp.multidict(dict_power2res)
        
        BioSupply = 0.
        TIMELIMITS = 600
        
        # build model
        m, take, y_flex, y_be, y_ccs, y_retire, cf, take = build_model('model', power_station_id, 
                        PPs_hours, InsCapacity, lon, lat, operateYear, set_retrofitYr,
                        ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                        y_opt, take, res_point_id, 
                        resources, power2res, distance, EMISS_GOAL, gap_set, 
                        BioSupply, columnName, unitCoal, flex,
                        be, ccs, retire, ELEC_GOAL, elecPrice, TIMELIMITS)
        
        # name, power_station_id, PPs_hours, InsCapacity, lon, lat, operateYear, set_retrofitYr, ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, y_opt, take, res_point_id, resources, power2res, distance, EMISS_GOAL, gap_set, BioSupply, columnName, unitCoal, flex,be, ccs, retire, ELEC_GOAL, elecPrice='model', power_station_id, PPs_hours, InsCapacity, lon, lat, operateYear, set_retrofitYr, ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, y_opt, take, res_point_id, resources, power2res, distance, EMISS_GOAL, gap_set, BioSupply, columnName, unitCoal, flex,be, ccs, retire, ELEC_GOAL, elecPrice  
        # solve the results for province
        # if m.status == GRB.OPTIMAL or m.objVal != float('-inf'):
        try:
        # if m.status == GRB.OPTIMAL:
            # check_write_results write excel to output directory
            pp_dict_out = update_results(m, pp_dict1, take, y_flex, y_be, y_ccs, y_retire, cf, distance, set_retrofitYr,'Value')
            check_results(pp_dict_out, EMISS_GOAL, ELEC_GOAL, set_retrofitYr)
            
            # save the pickle
            out_allProvPP_dict.update(pp_dict_out)
            
            # updae biomass taken data
            update_bio_dict = update_bioDict(bio_dict, take, dict_power2res)
            bio_dict = update_bio_dict.copy()
        
        # else:
        except:
            print('in %f year: prov:%s cannot be solved. The status:%s' % (year, prov_name, m.status))
            print('solve model in a brute way.')
            # force all the coal plants compulsory retired, and resolve the model again            
            tryagain_ppdict, force_retire_ppdict = brute_force_model(pp_dict1, set_retrofitYr, ELEC_GOAL)
            # convert the dict in the dict as one dict, the other dict use dataframe to store
            tmp_ppDict = twoDict_to_oneDict(tryagain_ppdict) 
            
            # varaibles for gurobi
            power_station_id, keyID, PPs_hours, InsCapacity, unitCoal, lon, lat, operateYear, pixelX, pixelY, dccs, y_opt, take, cost, emiss, pp_pos, ori_lcoeFrame, retrofitYear, flex, be, ccs, retire = gp.multidict(tmp_ppDict)
            
            # variable for biomass
            res_point_id, resources, res_loc = gp.multidict(bio_dict)
            
            # distance matrix
            dict_power2res = generate_disDict(pp_pos, res_loc, radius_limit, resolution)
            power2res, distance = gp.multidict(dict_power2res)
            
            BioSupply = 0.
            
            # build model
            m, take, y_flex, y_be, y_ccs, y_retire, cf, take = build_model('model', power_station_id, 
                            PPs_hours, InsCapacity, lon, lat, operateYear, set_retrofitYr,
                            ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                            y_opt, take, res_point_id, 
                            resources, power2res, distance, EMISS_GOAL, gap_set, 
                            BioSupply, columnName, unitCoal, flex,
                            be, ccs, retire, ELEC_GOAL, elecPrice, TIMELIMITS)
            
            if m.status == GRB.OPTIMAL:
                # check_write_results write excel to output directory
                pp_dict_out = update_results(m, tryagain_ppdict, take, y_flex, y_be, y_ccs, y_retire, cf, distance, set_retrofitYr,'Value')
                pp_dict_out.update(force_retire_ppdict)
                check_results(pp_dict_out, EMISS_GOAL, ELEC_GOAL, set_retrofitYr)
                
                # save the pickle
                out_allProvPP_dict.update(pp_dict_out)
                
                # updae biomass taken data
                update_bio_dict = update_bioDict(bio_dict, take, dict_power2res)
                bio_dict = update_bio_dict.copy()
            
            
            # if still cannot find the optimal solution, shut down all plants
            else: 
                print('brute force also fail, shut down all plants.')
                pp_dict_out = shut_down(pp_dict1, set_retrofitYr)
                check_results(pp_dict_out, EMISS_GOAL, ELEC_GOAL, set_retrofitYr)
                out_allProvPP_dict.update(pp_dict_out)               

    
    out_allProvPP_dict1 = write_results(out_allProvPP_dict, set_retrofitYr)
    visulize_results(set_retrofitYr)
    # write pickle file; 
    # pkl to input file and include new plants
    write_PPs_4nextYrs_pkl(out_allProvPP_dict1, set_retrofitYr)
    
    end = time.time()
    print('Running time for one year: %.1f minitue' % ((end - start)/60))
        
end0 = time.time() 
print('Running time for one pathway: %.1f minute' % ((end0 - start0)/60))      

# sys.stdout.flush()
# sys.stdout.close()