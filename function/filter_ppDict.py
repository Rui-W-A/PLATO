# -*- coding: utf-8 -*-
"""
Created on Sun Mar 10 16:15:06 2024

@author: vicke
"""

import numpy as np
import pandas as pd

def filter_pp(pp_dict, currentYrs):
    pp_dict_out = pp_dict.copy()
    for i in pp_dict.keys():
        inputYrs = pp_dict[i]['year']
        retire_opt = pp_dict[i]['retire']
        if inputYrs > currentYrs:
            del pp_dict_out[i]
            print('del %.f: planned' % i)
        elif inputYrs + 40 <= currentYrs:
            del pp_dict_out[i]
            print('del %.f: natural retire' % i)
        # if it is retire
        elif retire_opt[0] == 1:
            del pp_dict_out[i]
            print('del %.f: compulsory retire' % i)
            
    return pp_dict_out

def twoDict_to_oneDict(pp_dict):
    columnsPP = ['keyID', 'hours', 'Capacity_kw', 'CoalUnit_g/kwh',
            'lon', 'lat', 'year', 'pixelX','pixelY','ccsDis_km',
            'option', 'take','cost','emiss','pos','retrofitYear', 'flex','be','ccs','retire']
    
    tmp_ppDict = dict()
    
    for i in pp_dict.keys():
        power_station_id = pp_dict[i]['keyID']
        hours = pp_dict[i]['hours']
        Capacity_kw = pp_dict[i]['Capacity_kw']
        CoalUnit = pp_dict[i]['CoalUnit_g/kwh']
        lon = pp_dict[i]['lon']
        lat = pp_dict[i]['lat']
        year = pp_dict[i]['year']
        pixelX = pp_dict[i]['pixelX']
        pixelY = pp_dict[i]['pixelY']
        ccsDis_km = pp_dict[i]['ccsDis_km']
        option = pp_dict[i]['option']
        take = pp_dict[i]['take']
        cost = pp_dict[i]['C2020']
        emiss = pp_dict[i]['E2020']
        pos = pp_dict[i]['pos']
        lcof_df = pp_dict[i]['lcoe_df']
        retrofitYear = pp_dict[i]['year']
        flex = pp_dict[i]['flex']
        be = pp_dict[i]['be']
        ccs = pp_dict[i]['ccs']
        retire = pp_dict[i]['retire']
        
        tmp_add_list = [power_station_id, hours, Capacity_kw, CoalUnit, lon, lat, year, 
                       pixelX, pixelY, ccsDis_km, option, take, cost, 
                       emiss, pos, lcof_df, retrofitYear, flex, be, ccs, retire]
        # print(tmp_add_list)
        tmp_ppDict.update({i: tmp_add_list})
    
    return tmp_ppDict