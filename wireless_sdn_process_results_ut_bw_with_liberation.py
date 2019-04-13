from collections import Counter
import wireless_sdn_utils as utils
import re
import xlsxwriter
import wireless_sdn_replay_helper
from wireless_sdn_requests import Task
import wireless_sdn_replay_helper as replay

sw_openflow = -1
sw_group = 4
alpha2 = 10
alpha3 = 5 * alpha2
if sw_openflow == -1:
    # tag = '_no_ma'
    tag = ''
else:
    tag = '_sw_' + str(sw_openflow) + '_' + str(sw_group) + '_alpha2_' + str(10 * alpha2)

list_beta = [0.0, 1.0][1:]
# list_beta = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
list_arrival_rate = [i / 100.00 for i in range(1, 5, 1)][1:2]
list_nm_id = [2]
list_is_ilp = [0, 1][1:]
list_is_ps  = [0, 1][:1]

prob_cx = 0.9
prob_mt = 0.1
prob_ch = 0.9

list_str_generation_population = ['_np_20_ng_20', '']

def get_total_bandwdith(nm_id, is_ilp, is_ps, arrival_rate, beta):
    ilp_ga = {0: "_ga", 1: "_ilp"}[is_ilp]
    _str_ps = {0: "", 1: "_ps_01"}[is_ps]
    iwqos = {0: 'wireless_sdn_results', 1: 'wireless_sdn_iwqos/interference', 2: 'wireless_sdn_jwqos_200'}[2]

    str_generation_population = list_str_generation_population[is_ilp]

    args = ('./' + iwqos + '/' + "00_replay_nm_"
            + str(nm_id) + "_rate_0" + utils.demical_to_str(arrival_rate, len_demical=2) +
            "_beta_" + utils.demical_to_str(beta) + _str_ps + str_generation_population + ilp_ga + tag + ".txt", "r")
    output_file_name = './' + iwqos + '/data_total_bandwidth' + tag + '_beta_1.txt'
    fo = open(*args)
    bandwidth = 0
    hmap = {}
    ut = 0
    for line in fo.readlines():
        words = filter(lambda x: len(x) > 0, re.split(',| |\n|{|}', line))
        i = 0
        if 'Elapsed' in words:
            hmap[ut] = bandwidth
            bandwidth = 0
            continue
        if 'UT' in words:
            ut = int(words[2])
            continue
        for w in words:
            if 'total_bw_consumed:' in w:
                i += 1
                bandwidth = int(words[i])
                break
            i += 1
    fo.close()
    hmap[ut] = bandwidth

    req_tasks = wireless_sdn_replay_helper.load_req_tasks("wireless_sdn_pickles/req_nodes_20_rate_002/1")
    hd = req_tasks.hd

    total_bw_with_liberation = 0
    while len(hd):
        (_time, (_t, task)) = hd.popitem()
        current_time = task.task_time
        if _time != current_time or _time != _t:
            print("NOT EQUAL")
            return

        if _time > req_tasks.time_max:
            break

        if task.flag_new_requests:
            (pop_time, requests) = task.tuple_poptime_requests

            total_bw_with_liberation += hmap[current_time]

            (_, task_future) = hd.setdefault(pop_time, (pop_time, Task()))
            task_future.task_time = pop_time
            task_future.flag_expire_requests = True
            if hmap[current_time] > 0:
                task_future.expire_ilp.append(hmap[current_time])

        if task.flag_expire_requests:
            for resource_expire_ilp in task.expire_ilp:
                total_bw_with_liberation -= resource_expire_ilp

        fa = open(output_file_name, "a")
        fa.write(str(current_time) + ' ' + str(total_bw_with_liberation) + '\n')
        fa.close()

def run_all():
    for nm_id in list_nm_id:
        for is_ilp in list_is_ilp:
            if is_ilp:
                for is_ps in list_is_ps:
                    for arrival_rate in list_arrival_rate:
                        for beta in list_beta:
                            get_total_bandwdith(nm_id, is_ilp, is_ps, arrival_rate, beta)

if __name__ == "__main__":
    run_all()

