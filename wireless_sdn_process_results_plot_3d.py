# coding: utf-8
import pandas as pd
import wireless_sdn_utils as utils

def read_and_write(nm_id, num_population, num_generation, prob_cx=0.9, prob_mt=0.1, prob_ch=0.9):
    tag = '_cx_' + utils.demical_to_str(prob_cx) + '_mt_0' + \
           utils.demical_to_str(prob_mt, len_demical=2) + '_ch_0' + utils.demical_to_str(prob_ch, len_demical=2)
    str_generation_population = '_np_' + str(num_population) + '_ng_' + str(num_generation)
    exel_file_name = './wireless_sdn_results/' + 'GA' + str_generation_population + \
                 '_NM_' + str(nm_id) + tag + '_BETA.xlsx'
    df = pd.read_excel(exel_file_name)
    acceptance_rate = float(df['SuccessRate100'])
    return (num_population, num_generation, acceptance_rate)

if __name__ == '__main__':
    list_num_population = [i for i in range(4, 21, 4)][:]
    list_num_generation = [i for i in range(4, 21, 4)][:]
    result = []
    for num_population in list_num_population:
        for num_generation in list_num_generation:
            result.append(read_and_write(2, num_population, num_generation))
    print(result)
    args = ("wireless_sdn_results/plot/plot3d/" + "data_plot3d.txt", "w")
    fo = open(*args)
    for r in result[:-1]:
        fo.write(str(r[0]) + ' ' + str(r[1]) + ' ' + str(r[2]) + '\n')
    r = result[-1]
    fo.write(str(r[0]) + ' ' + str(r[1]) + ' ' + str(r[2]))
    fo.close()

