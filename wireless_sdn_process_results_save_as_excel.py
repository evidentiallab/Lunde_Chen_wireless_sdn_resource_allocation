from collections import Counter
import wireless_sdn_utils as utils
import re
import xlsxwriter

sw_openflow = -1
sw_group = 4
alpha2 = 10
alpha3 = 5 * alpha2
if sw_openflow == -1:
    tag = ''
else:
    tag = '_sw_' + str(sw_openflow) + '_' + str(sw_group) + '_alpha2_' + str(10 * alpha2)

list_beta = [0.0, 1.0][:]
# list_beta = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
list_arrival_rate = [i / 100.00 for i in range(1, 5, 1)][:]
list_nm_id = [2]
list_is_ilp = [0, 1][:1]
list_is_ps  = [0, 1][:1]

prob_cx = 0.9
prob_mt = 0.1
prob_ch = 0.9

list_str_generation_population = ['_np_20_ng_20', '']


def get_total_switch_resources(nm_id, is_ilp, is_ps, arrival_rate, beta):
    ilp_ga = {0: "_ga", 1: "_ilp"}[is_ilp]
    _str_ps = {0: "", 1: "_ps_01"}[is_ps]
    iwqos = {0: 'wireless_sdn_results', 1: 'wireless_sdn_iwqos', 2: 'wireless_sdn_Jwqos'}[2]

    str_generation_population = list_str_generation_population[is_ilp]

    args = ('./' + iwqos + '/' + "00_replay_nm_"
            + str(nm_id) + "_rate_0" + utils.demical_to_str(arrival_rate, len_demical=2) +
            "_beta_" + utils.demical_to_str(beta) + _str_ps + str_generation_population + ilp_ga + tag + ".txt", "r")
    fo = open(*args)
    total_openflow_entry = 0
    total_group_entry = 0
    for line in fo.readlines():
        words = filter(lambda x: len(x) > 0, re.split(',| |\n|{|}', line))
        i = 0
        _len = len(words)
        for w in words:
            if 'dict_node_id_openflow_table_decrease:' in w:
                i += 1
                while ':' in words[i] and 'dict' not in words[i]:
                    i += 1
                    total_openflow_entry += int(words[i])
                    i += 1
                    if i >= _len:
                        break
                break
            i += 1
        i = 0
        for w in words:
            if 'dict_node_id_group_table_decrease:' in w:
                i += 1
                while ':' in words[i] and 'dict' not in words[i]:
                    i += 1
                    total_group_entry += int(words[i])
                    i += 1
                    if i >= _len:
                        break
                break
            i += 1
    return (total_openflow_entry, total_group_entry)


def main_matrix(nm_id, is_ilp, is_ps):
    ilp = {0: "_ga", 1: "_ilp"}[is_ilp]
    _str_ps = {0: "", 1: "_ps_01"}[is_ps]
    iwqos = {0: 'wireless_sdn_results', 1: 'wireless_sdn_iwqos', 2: 'wireless_sdn_Jwqos'}[2]
    error = False

    str_generation_population = list_str_generation_population[is_ilp]

    global tag
    if is_ilp == 0:
        tag += '_cx_' + utils.demical_to_str(prob_cx) + '_mt_0' + \
               utils.demical_to_str(prob_mt, len_demical=2) + '_ch_0' + utils.demical_to_str(prob_ch, len_demical=2)

    output_file_name = './' + iwqos + '/'
    if 'ilp' in ilp:
        output_file_name += 'ILP_'
    else:
        output_file_name += 'GA' + str_generation_population + '_'
    if len(_str_ps):
        output_file_name += 'PS_'
    output_file_name += 'NM_' + str(nm_id) + tag + '.xlsx'

    import numpy as np
    mat = np.ones((len(list_arrival_rate), len(list_beta), 12))
    j = 0
    for arrival_rate in list_arrival_rate:
        k = 0
        for beta in list_beta:
            args = ('./' + iwqos + '/' + "00_replay_nm_"
                      + str(nm_id) + "_rate_0" + utils.demical_to_str(arrival_rate, len_demical=2) +
                      "_beta_" + utils.demical_to_str(beta) + _str_ps + str_generation_population + ilp + tag + ".txt", "r")
            fo = open(* args)
            wordcount = Counter(fo.read().split())
            mat[(j, k, 0)] = float(wordcount["False"])
            mat[(j, k, 1)] = float(wordcount["True"])
            mat[(j, k, 2)] = float(100.000 * mat[(j, k, 1)] / (mat[(j, k, 0)] + mat[(j, k, 1)]))
            total_bw = 0.0
            total_interf = 0.0
            UT_last = -1
            fo = open(*args)
            for line in fo.readlines():
                words = filter(lambda x: len(x) > 0, re.split(',| |\n|:', line))
                i = 0
                for w in words:
                    i += 1
                    if 'total_bw_consumed' in w:
                        total_bw += float(words[i])
                    elif 'total_interference_brought' in w:
                        total_interf += float(words[i])
                    elif 'UT' in w:
                        UT_last = float(words[i])
            (total_openflow_entry, total_group_entry) = get_total_switch_resources(nm_id, is_ilp, is_ps, arrival_rate, beta)
            mat[(j, k, 3)] = total_bw
            mat[(j, k, 4)] = total_bw / mat[(j, k, 1)]
            mat[(j, k, 5)] = total_interf
            mat[(j, k, 6)] = total_interf / mat[(j, k, 1)]
            mat[(j, k, 7)] = UT_last
            mat[(j, k, 8)] = total_openflow_entry
            mat[(j, k, 9)] = float(mat[(j, k, 8)] / (mat[(j, k, 1)]))
            mat[(j, k, 10)] = total_group_entry
            mat[(j, k, 11)] = float(mat[(j, k, 10)] / (mat[(j, k, 1)]))
            fo.close()
            # if int(UT_last) not in [9873, 9998, 9979, 9984, 9991, 9997, 9927, 9939]:
            #     error = True
            k += 1
        j += 1
    workbook = xlsxwriter.Workbook(output_file_name)
    worksheet = workbook.add_worksheet()
    worksheet.write_row(0, 0, ['Arrival Rate', 'Beta', "Failure", "Success", "SuccessRate100",
                               "Total bandwidth", 'Average bandwidth', 'Total interference',
                               'Average interference', 'UT_last',
                               'Total OF entries', 'Average OF entries',
                               'Total group entries', 'Average group entries'])
    row = 1
    j = 0
    for arrival_rate in list_arrival_rate:
        k = 0
        for beta in list_beta:
            worksheet.write_row(row, 0, [arrival_rate])
            worksheet.write_row(row, 1, [beta])
            worksheet.write_row(row, 2, mat[(j, k)])
            k += 1
            row += 1
        j += 1
    workbook.close()

    msg = ""
    for _mat in mat:
        for _line in _mat:
            for _value in _line[:-1]:
                msg += str(_value) + " "
            msg += str(_line[-1])
            msg += "\n"
    if error:
        msg += "THERE IS SOMETHING WRONG.\n"
    print(msg)


def run_all():
    for nm_id in list_nm_id:
        for is_ilp in list_is_ilp:
            if is_ilp:
                for is_ps in list_is_ps:
                    main_matrix(nm_id, is_ilp, is_ps)
            else:
                main_matrix(nm_id, is_ilp, 0)


if __name__ == "__main__":
    run_all()

