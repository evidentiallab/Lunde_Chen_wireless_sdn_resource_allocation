from __future__ import print_function
import pandas as pd
import os
import wireless_sdn_utils as utils

os.chdir('./wireless_sdn_test_sph_sw')

capacity_init = {1: 180, 2: 190}[1]
list_arrival_rate = [i / 100.00 for i in range(1, 5, 1)][1:2]
list_K = [2]
list_power = [1.5]
list_threshold = [30, 100]

list_K_sw = [2, 3, 5]
list_power_sw = [1.3, 1.5, 2, 3]
list_threshold_sw = [10, 30, 50, 100]
# list_threshold_sw = [10, 30, 50]
# list_threshold_sw = [100]
list_do_nothing = [0, 1]

sw_init = 70

for arrival_rate in list_arrival_rate:
    print('-------------------------------')
    res = []
    for K in list_K:
        for power in list_power:
            for threshold in list_threshold:
                for K_sw in list_K_sw:
                    for power_sw in list_power_sw:
                        for threshold_sw in list_threshold_sw:
                            for do_nothing in list_do_nothing:
                                _str_init = '_cp_' + str(capacity_init)
                                _str_sw_init = '_si_' + str(sw_init)
                                _str_K = '_K_' + str(K)
                                _str_power = '_pw_' + str(int(power * 10))
                                _str_threshold = '_th_' + str(threshold)
                                _str_K_sw = '_Ksw_' + str(K_sw)
                                _str_power_sw = '_pwsw_' + str(int(power_sw * 10))
                                _str_threshold_sw = '_thsw_' + str(threshold_sw)
                                _str_do_nothing = '_dn_' + str(do_nothing)

                                _head_name = "0_rep" + \
                                             "_nm_1" + "_rate_0" + utils.demical_to_str(arrival_rate, len_demical=2) + \
                                             "_beta_10" +  \
                                             "_sph" + _str_sw_init + _str_init + _str_K + _str_power + _str_threshold + \
                                             _str_K_sw + _str_power_sw + _str_threshold_sw + _str_do_nothing
                                data = pd.read_excel(_head_name + "_exel.xlsx")
                                success = list(data['AcceptRate'])[-1]
                                res.append((success, _head_name))
    res.sort(reverse=True)
    for (_suc, _head_n) in res[:min(len(res), 40)]:
        print(str(_suc), ' : ', _head_n, '\n')
