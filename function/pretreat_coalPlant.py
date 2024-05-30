# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 18:44:33 2024

@author: vicke
"""

import pandas as pd
import numpy as np
from function.cal_cost_df import Cal_lcoe_fromDF, Initial_CCS_lcoeDF, Initial_PP_lcoeDF
from function.cal_emiss import Emiss_BE, Emiss_PP, Emiss_CCS, Emiss_BECCS, Emiss_Retire
import math  
import matplotlib.pyplot as plt
import pickle
from function.cal_emiss1 import cal_emiss

def pretreat_coalPlant(num, elecPrice):

    filePath = 'input/Global-Coal-Plant-Tracker-January-2024.xlsx'
    resolution = 20 # km
    pp_data_GEM = pd.read_excel(filePath, sheet_name='Units', nrows=0)
    if num>0:
        pp_data_GEM = pd.read_excel(filePath, sheet_name='Units', nrows=num)
    else:
        pp_data_GEM = pd.read_excel(filePath, sheet_name='Units')
    columnName = 'Value'
    
    status_filter = ['announced', 'operating', 'construction', 'permitted', 'pre-permit']
    pp_data_China = pp_data_GEM[(pp_data_GEM['Country'] == 'China') & (pp_data_GEM['Status'].isin(status_filter))]
    if len(pp_data_China) == 0:
        print('please enlarge the input number')
        return
    
    columns_filter = ['Capacity factor','Capacity (MW)', 'Combustion technology', 'Longitude', 'Latitude',
                      'Subnational unit (province, state)', 'Status', 'Start year']
    pp_data = pp_data_China[columns_filter]
    
    pp_data['hours'] = pp_data['Capacity factor'] * 24 * 365
    pp_data['Capacity_kw'] = pp_data['Capacity (MW)'] * 1000
    pp_data = pp_data.rename(columns={'Longitude':'lon', 'Latitude': 'lat'})
    pp_data['ID'] = [x for x in range(len(pp_data))]
    
    
    # status: 'announced', 'operating', 'construction', 'permitted', 'pre-permit'
    # 'announced' = 2024 + 2 = 2026; 
    # 'construction' = 2024 + 1 = 2025; 
    # 'permitted' = 2024 + 3 = 2027;
    # 'pre-permit' = 2024 + 6 = 2030;
    
    pp_withYrs = pp_data[pp_data['Start year'].notnull()]
    pp_1 = pp_data[(pp_data['Status']=='announced')&(pp_data['Start year'].isnull())]
    pp_1['Start year'] = 2026
    pp_2 = pp_data[(pp_data['Status']=='construction')&(pp_data['Start year'].isnull())]
    pp_2['Start year'] = 2025
    pp_3 = pp_data[(pp_data['Status']=='permitted')&(pp_data['Start year'].isnull())]
    pp_3['Start year'] = 2027
    pp_4 = pp_data[(pp_data['Status']=='pre-permit')&(pp_data['Start year'].isnull())]
    pp_4['Start year'] = 2030
    pp_5 = pp_data[(pp_data['Status']=='operating')&(pp_data['Start year'].isnull())]
    pp_5['Start year'] = 2024 
    pp = pd.concat([pp_withYrs, pp_1, pp_2, pp_3, pp_4, pp_5], axis=0)
    pp['year'] = pp['Start year']
    pp = pp[pp['year']>1990]
    pp[(pp['year'] > 1990)&(pp['year'] <= 2022)]['Capacity (MW)'].sum()
    
    # calculate pp in which grid cell
    pp['pixelX'] = round((pp['lon'] - 70) / 0.01 / resolution)
    pp['pixelY'] = round((pp['lat'] - 15) / 0.01 / resolution)
    pp = pp.set_index(pp['ID'])
    
    # find the nearest carbon storage point and calculate the distance
    ccs_point = pd.read_excel('input/ccs.xlsx')
    for p in pp.index:
        lon_p = pp.loc[p, 'lon']
        lat_p = pp.loc[p, 'lat']
        
        dis_list = []
        for c in range(len(ccs_point)):
            lon_c = ccs_point.loc[c, 'POINT_X']
            lat_c = ccs_point.loc[c, 'POINT_Y']
            dis = math.sqrt((lon_p - lon_c)**2 + (lat_p - lat_c)**2) * 111
            dis_list.append(dis)
        
        dis_list.sort(reverse=False)
        tortuosity = 3.7
        pp.loc[p, 'ccsDis_km'] = dis_list[0] * tortuosity
    
    # calculate coal consumption amount
    # 'ultra-supercritical', 'supercritical', 'subcritical', 'unknown', 'CFB', 'IGCC', 'ultra-supercritical/ccs'
    tmp1 = pp[(pp['Combustion technology'] == 'ultra-supercritical')&(pp['Capacity (MW)'] >= 600)]
    tmp1['CoalUnit_g/kwh'] = 285
    tmp2 = pp[(pp['Combustion technology'] == 'ultra-supercritical')&(pp['Capacity (MW)'] < 600)]
    tmp2['CoalUnit_g/kwh'] = 293
    tmp3 = pp[(pp['Combustion technology'] == 'supercritical')&(pp['Capacity (MW)'] >= 300)]
    tmp3['CoalUnit_g/kwh'] = 300
    tmp4 = pp[(pp['Combustion technology'] == 'supercritical')&(pp['Capacity (MW)'] < 300)]
    tmp4['CoalUnit_g/kwh'] = 308
    tmp5 = pp[(pp['Combustion technology'] == 'subcritical')&(pp['Capacity (MW)'] >= 300)]
    tmp5['CoalUnit_g/kwh'] = 314
    tmp6 = pp[(pp['Combustion technology'] == 'subcritical')&(pp['Capacity (MW)'] < 300)]
    tmp6['CoalUnit_g/kwh'] = 323
    tmp7 = pp[(pp['Combustion technology'] == 'CFB')|(pp['Combustion technology'] == 'CFB')]
    tmp7['CoalUnit_g/kwh'] = 290
    tmp8 = pp[(pp['Combustion technology'] == 'IGCC')|(pp['Combustion technology'] == 'ultra-supercritical/ccs')]
    tmp8['CoalUnit_g/kwh'] = 270
    pp = pd.concat([tmp1, tmp2, tmp3, tmp4, tmp5, tmp6, tmp7, tmp8], axis=0)
    pp['pp'] = [(int(1), int(x)) for x in pp['year']]
    pp['flex'] = [(int(0), int(9999)) for i in range(len(pp))]
    pp['be'] = [(int(0), int(9999)) for i in range(len(pp))]
    pp['ccs'] = [(int(0), int(9999)) for i in range(len(pp))]
    pp['retire'] =  [(int(0), int(9999)) for i in range(len(pp))]
    
    tmp1 = pp[pp['Combustion technology'] == 'ultra-supercritical/ccs']
    if len(tmp1)>0:
        tmp1['option'] = 'CCS'
        tmp1['E2020'] = tmp1.apply(lambda x: Emiss_CCS(x['Capacity_kw'], x['hours'], x['year'], 2020, x['CoalUnit_g/kwh']), axis=1)
        tmp1['ccs'] = [(int(1), int(x)) for x in tmp1['year']]
        tmp2 = pp[pp['Combustion technology'] != 'ultra-supercritical/ccs']
        tmp2['option'] = 'PP'
        tmp2['E2020'] = tmp2.apply(lambda x: Emiss_PP(x['Capacity_kw'], x['hours'], x['year'], 2020, x['CoalUnit_g/kwh']), axis=1)
        pp = pd.concat([tmp1, tmp2], axis=0)
    else:
        tmp2 = pp[pp['Combustion technology'] != 'ultra-supercritical/ccs']
        tmp2['pp'] = [(int(1), int(x)) for x in tmp2['year']]
        tmp2['E2020'] = tmp2.apply(lambda x: Emiss_PP(x['Capacity_kw'], x['hours'], x['year'], 2020, x['CoalUnit_g/kwh']), axis=1)
        tmp2['option'] = 'PP'
        pp = tmp2.copy()
        
    # pretreat
    pp['take'] = 0.
    
    # merge unit to plant
    key_info = ['hours', 'CoalUnit_g/kwh', 'lon', 'lat', 'year', 
                'pixelX','pixelY','ccsDis_km', 'option', 'pp',
                'flex','be','ccs','retire','take']
    
    pp_group = pp.groupby(by=key_info)
    pp_group_sum = pp_group.sum()
    pp_tmp = pp_group_sum.loc[:,['Capacity_kw', 'E2020']]
    pp = pp_tmp.reset_index()
    pp['ID'] = [x for x in range(len(pp))]    
    
    # save results
    pick = ['ID', 'hours', 'Capacity_kw', 'CoalUnit_g/kwh',
            'lon', 'lat', 'year', 'pixelX','pixelY','ccsDis_km',
            'option','E2020','take', 'pp', 'flex','be','ccs','retire']   
    pp_out = pp[pick]
    
    pp_out['pos'] = pp_out[['pixelX', 'pixelY']].apply(tuple, axis=1)
    pp_out['cf'] = [1 for x in range(len(pp_out))]
    pp_out['take_dis'] = [0 for x in range(len(pp_out))]
    
    # yrEmiss_10_6t, totalProfit_10_9dollar, yrElec_10_6kWh    
    pp_out['yrEmiss_10_6t'] = pp_out.apply(lambda x: cal_emiss(x['be'][0], 0, x['ccs'][0], 0,
                            x['retire'][0], x['cf'], x['Capacity_kw'], x['hours'], x['take'],
                            0, x['CoalUnit_g/kwh']) / pow(10,6), axis=1)

    pp_out['yrElec_10_9kwh'] = pp_out.apply(lambda x: x['Capacity_kw'] * x['hours'] * 40 / pow(10,9), axis=1)
    
    pp_dict = pp_out.set_index('ID').T.to_dict('dict')
    
    pp_dict1 = pp_dict.copy()
    
    # calculate original lcoe
    for i in pp_dict.keys():
        faci_type = pp_dict[i]['option']
        # print(faci_type)
        if faci_type == 'CCS':
            lcoe_df = Initial_CCS_lcoeDF(pp_dict[i]['Capacity_kw'], pp_dict[i]['hours'], pp_dict[i]['ccsDis_km'], pp_dict[i]['year'], 2020, 'Value', pp_dict[i]['CoalUnit_g/kwh'])
            lcoe_p = Cal_lcoe_fromDF(lcoe_df)
            elecAmount = pp_dict[i]['yrElec_10_9kwh']
            pp_dict1[i].update({'C2020': lcoe_p})
            pp_dict1[i].update({'lcoe_df': lcoe_df})
            pp_dict1[i].update({'totalCost_10_9dollar': (elecPrice - lcoe_p) * elecAmount})
            pp_out.loc[i,'C2020'] = lcoe_p
            pp_out.loc[i,'totalCost_10_9dollar'] = (elecPrice - lcoe_p) * elecAmount
            
        elif faci_type == 'PP':
            lcoe_df = Initial_PP_lcoeDF(pp_dict[i]['Capacity_kw'], pp_dict[i]['hours'], pp_dict[i]['year'], 2020, 'Value')
            lcoe_p = Cal_lcoe_fromDF(lcoe_df)
            elecAmount = pp_dict[i]['yrElec_10_9kwh']
            pp_dict1[i].update({'C2020': lcoe_p})
            pp_dict1[i].update({'lcoe_df': lcoe_df})
            pp_dict1[i].update({'totalCost_10_9dollar': lcoe_p * elecAmount})
            pp_out.loc[i,'C2020'] = lcoe_p
            pp_out.loc[i,'totalCost_10_9dollar'] = lcoe_p * elecAmount
    
    
    # save it as the pretreat plants
    with open('input/CoalPlants/powerplants_2020.pkl','wb') as f:
        pickle.dump(pp_dict1, f)
        
    # save a csv file
    pp_out1 = pp_out.drop('pos', axis=1)
    pp_out1.to_csv('input/pp_all.csv')
    pp_out1.to_csv('output/pp_all_2020.csv')
    
    print('finish pretreatment')
    print('total number of coal plants: %.0f' % len(pp_out1))
    
    return