# coding: utf-8
from __future__ import print_function
import random
import subprocess
import time
import os

python = {1: "python ", 2: "pypy "}[2]
method = {1: "ilp.py ", 2: "ga.py ", 3: "sph.py "}[3]

# common parameters for ILP, GA and SPH
sw_openflow = -1       # -1: keep as in the generated graph model.
                       # sw = 70, arrival = 0.02: check the effect of switch resource balancing.
sleep_time = {"N": 0, "W": 26000, "Y": 36000}["N"]
list_nm_id = [1]
list_arrival_rate = [i / 100.00 for i in range(1, 5, 1)][:]
list_beta = [0.0, 1.0][1:]  # beta for interference accounting. DON'T try with beta = 2, 3, 4 etc. Doesn't work!!!
list_path_split = [0.1, 1][1:]
list_capacity_init = [170, 180, 190]  # 180 for normal cases
list_use_multicast_advantage = [0, 1][1:]   # 0 for no, 1 for yes 
list_sw_resource_balancing = [0, 15][1:]    # 0: no sw resource balancing. 15 by default.
list_load_balancing = [0, 5][1:]  # the default value is 5. [0, 3] are options.
min_max_clique_utilization_scheme = 2 # 0: no load balancing, which has the same effect as list_load_balancing = 0
                                      # 1: minimize max
                                      # 2: minimize (max - min)  (* the default value is 2, as this gives the best results.)

# GA parameters
prob_cx = 0.9
prob_mt = 0.1
prob_ch = 0.9
# list_num_population = [i * 10 for i in range(1, 6)][4:5]
list_num_population = [18]
# list_num_generation = [i * 10 for i in range(1, 6)][4:5]
list_num_generation = [-1]
multiplier_factor = 1.5 # by default 1.5.

# SPH and GA parameters
list_K = [2]  # By default 2. Other option: 3 gives good results as well. No need to mention in the paper.
list_power = [1.5]  # 1.5 is good. 1.3 is good also.
list_power_else = [1.1] # default value: 1.1
list_threshold = [30, 100][:]  # By default, should be 30. Other options: 10, 50 and 100.
                                # At threshold = 100, there is no load balancing. Hence no need for power = 1.

list_K_sw = [4]  # default value: 2
list_power_sw = [2]  # default value: 1.5
list_power_sw_else = [1.1]  # default value: 1.1
list_threshold_sw = [30, 100][:]  # default value: 100

list_do_nothing = [0]  # default: 0, as this gives better results in 100% of cases. The other option: 1.

reverse_metric = 1
if reverse_metric == 1:
    list_threshold = [100]
    list_threshold_sw = [100]

if __name__ == "__main__":
    sw_group = -1  # -1: keep as in the generated graph model
    if sw_openflow != -1:
        sw_group = 2000
    alpha2 = 1
    alpha3 = 5 * alpha2
    script_name = "wireless_sdn_bash_auto_generated.sh"

    alpha3 = 1
    _tag = ''

    list_sph_cost_scheme = [0]  # SPH only. By default is 0, as this gives good results in 100% of cases. Other option: 1.
    list_one_by_one_overload_avoidance_strategy = [1]  # For GA only. Default is [1].
    fo = open(script_name, "w")
    fo.write("#! /bin/bash\n\n")
    fo.write("sleep " + str(sleep_time) + "\n")
    for nm_id in list_nm_id:
        for arrival_rate in list_arrival_rate:
            for beta in list_beta:
                for use_multicast_advantage in list_use_multicast_advantage:
                    for capacity_init in list_capacity_init:
                        if "sph" in method:
                            list_sw_resource_balancing = [0]
                        for sw_resource_balancing in list_sw_resource_balancing:
                            if min_max_clique_utilization_scheme == 0 or "sph" in method:
                                list_load_balancing = [0]
                            for load_balancing in list_load_balancing:
                                _arg_path_split = ""
                                if sw_openflow == -1:
                                    tag = _tag + ''
                                else:
                                    tag = _tag + '_si_' + str(sw_openflow)
                                if "ilp" in method:
                                    for path_split in list_path_split:
                                        _arg_path_split = " " + str(path_split)
                                        fo.write(
                                            "nohup " + python + "wireless_sdn_replay_mode_" + method +
                                            str(nm_id) + " " + str(capacity_init) + " " + str(arrival_rate)
                                            + " " + str(beta) + ' ' + str(alpha2) + ' '
                                            + str(alpha3) + ' ' + str(sw_openflow) + ' '
                                            + str(sw_group) + ' \'' + tag + '\' '
                                            + _arg_path_split + ' ' + str(use_multicast_advantage)
                                            + ' ' + str(load_balancing)
                                            + ' ' + str(min_max_clique_utilization_scheme)
                                            + ' ' + str(sw_resource_balancing)
                                            + " > ~/hi" + str(random.randint(1000, 9999)) + ".txt &\n")
                                elif "ga" in method:
                                    if sw_openflow == -1:
                                        tag = _tag + ''
                                    else:
                                        tag = _tag + '_si_' + str(sw_openflow)
                                    # tag += str('_cx_' + utils.demical_to_str(prob_cx) + '_mt_0' +
                                    #        utils.demical_to_str(prob_mt, len_demical=2) + '_ch_0' + utils.demical_to_str(prob_ch, len_demical=2))
                                    for num_population in list_num_population:
                                        for num_generation in list_num_generation:
                                            if num_generation == -1:
                                                num_generation = num_population
                                            for one_by_one_overload_avoidance_strategy in list_one_by_one_overload_avoidance_strategy:
                                                for K in list_K:
                                                    for power in list_power:
                                                        for threshold in list_threshold:
                                                            for K_sw in list_K_sw:
                                                                for power_sw in list_power_sw:
                                                                    for threshold_sw in list_threshold_sw:
                                                                        for power_else in list_power_else:
                                                                            for power_sw_else in list_power_sw_else:
                                                                                fo.write(
                                                                                    "nohup " + python + "wireless_sdn_replay_mode_" + method +
                                                                                    str(nm_id) + " " + str(capacity_init) + " " + str(arrival_rate)
                                                                                    + " " + str(beta) + ' ' + str(alpha2) + ' '
                                                                                    + str(alpha3) + ' ' + str(sw_openflow) + ' ' + str(sw_group) + ' ' + str(num_population)
                                                                                    + ' ' + str(num_generation) + ' \'' + tag + '\' ' + str(prob_cx)
                                                                                    + ' ' + str(prob_mt) + ' ' + str(prob_ch) + ' ' + str(use_multicast_advantage)
                                                                                    + ' ' + str(one_by_one_overload_avoidance_strategy)
                                                                                    + ' ' + str(multiplier_factor)
                                                                                    + ' ' + str(load_balancing)
                                                                                    + ' ' + str(min_max_clique_utilization_scheme)
                                                                                    + ' ' + str(sw_resource_balancing)
                                                                                    + ' ' + str(K)
                                                                                    + ' ' + str(power)
                                                                                    + ' ' + str(threshold)
                                                                                    + ' ' + str(K_sw)
                                                                                    + ' ' + str(power_sw)
                                                                                    + ' ' + str(threshold_sw)
                                                                                    + ' ' + str(power_else)
                                                                                    + ' ' + str(power_sw_else)
                                                                                    + " > ~/hi" + str(random.randint(1000, 9999)) + ".txt &\n")
                                else:
                                    for K in list_K:
                                        for power in list_power:
                                            for threshold in list_threshold:
                                                for sph_cost_scheme in list_sph_cost_scheme:
                                                    for K_sw in list_K_sw:
                                                        for power_sw in list_power_sw:
                                                            for threshold_sw in list_threshold_sw:
                                                                for do_nothing in list_do_nothing:
                                                                    for power_else in list_power_else:
                                                                        for power_sw_else in list_power_sw_else:
                                                                            fo.write(
                                                                                "nohup " + python + "wireless_sdn_replay_mode_" + method +
                                                                                str(nm_id) + " " + str(capacity_init) + " " + str(arrival_rate)
                                                                                + " " + str(beta) + ' ' + str(alpha2) + ' '
                                                                                + str(alpha3) + ' ' + str(sw_openflow) + ' ' + str(sw_group) + ' '
                                                                                + str(use_multicast_advantage)
                                                                                + ' ' + str(K)
                                                                                + ' ' + str(power)
                                                                                + ' ' + str(threshold)
                                                                                + ' ' + str(sph_cost_scheme)
                                                                                + ' ' + str(K_sw)
                                                                                + ' ' + str(power_sw)
                                                                                + ' ' + str(threshold_sw)
                                                                                + ' ' + str(do_nothing)
                                                                                + ' ' + str(power_else)
                                                                                + ' ' + str(power_sw_else)
                                                                                + ' ' + str(reverse_metric)
                                                                                + " > ~/hi" + str(random.randint(1000, 9999)) + ".txt &\n")
    fo.close()

    time.sleep(0.05)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir_path)
    subprocess.Popen(["bash", script_name])

