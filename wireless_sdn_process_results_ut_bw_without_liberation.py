# coding: utf-8
from collections import Counter
import wireless_sdn_utils as utils
import re
import xlsxwriter

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
    iwqos = {0: 'wireless_sdn_results', 1: 'wireless_sdn_iwqos/multicast_advantage'}[1]

    str_generation_population = list_str_generation_population[is_ilp]

    args = ('./' + iwqos + '/' + "00_replay_nm_"
            + str(nm_id) + "_rate_0" + utils.demical_to_str(arrival_rate, len_demical=2) +
            "_beta_" + utils.demical_to_str(beta) + _str_ps + str_generation_population + ilp_ga + tag + ".txt", "r")
    output_file_name = './' + iwqos + '/data_total_bandwidth' + tag + '.txt'
    fo = open(*args)
    total_bandwidth = 0
    ut = 0
    for line in fo.readlines():
        words = filter(lambda x: len(x) > 0, re.split(',| |\n|{|}', line))
        i = 0
        if 'Elapsed' in words:
            fa = open(output_file_name, "a")
            fa.write(str(ut) + ' ' + str(total_bandwidth) + '\n')
            fa.close()
            continue
        if 'UT' in words:
            ut = words[2]
            continue
        for w in words:
            if 'total_bw_consumed:' in w:
                i += 1
                total_bandwidth += int(words[i])
                break
            i += 1
    fa = open(output_file_name, "a")
    fa.write(str(ut) + ' ' + str(total_bandwidth) + '\n')
    fa.close()
    fo.close()

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

