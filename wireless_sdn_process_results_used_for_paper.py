# coding: utf-8
import pandas as pd
import wireless_sdn_utils as utils

sw_openflow = -1
sw_group = -1
alpha2 = 0
alpha3 = 5 * alpha2
if sw_openflow == -1:
    tag = ''
else:
    tag = '_sw_' + str(sw_openflow) + '_' + str(sw_group) + '_alpha2_' + str(10 * alpha2)

class ProcessResultsForPaper(object):
    def __init__(self):
        self.data_all = {}
        self.ga = {1: "GA_NM_1", 2: "GA_NM_2", 3: "GA_NM_3"}
        self.ilp = {1: "ILP_NM_1", 2: "ILP_NM_2", 3: "ILP_NM_3"}
        self.ilp_ps = {1: "ILP_PS_NM_1", 2: "ILP_PS_NM_2", 3: "ILP_PS_NM_3"}
        for _dict_name in [self.ga, self.ilp, self.ilp_ps]:
            for _, _name in _dict_name.items():
                self.data_all[_name] = pd.read_excel("./wireless_sdn_results/" + _name + tag + ".xlsx")
        self.data_all[self.ga[1]].head(10)
        print(type(self.data_all[self.ga[1]]))

    def examples(self):
        df = self.data_all[self.ga[1]]
        print(df.loc[df['Arrival Rate'] == 0.04])
        df3 = self.data_all[self.ga[3]]
        print(df3.loc[df3['Arrival Rate'] == 0.06])
        df3.where(df3["Beta"] == 0.2)
        d = df3.loc[df3['Arrival Rate'] == 0.06]
        e = d.loc[d['Beta'] == 0.2]
        print(df3[df3.Success >= 99])
        print(df3[df3.Beta == 0.2])
        df3.query('Beta == 0.2 and Success >= 99')

    def get_results_GA_vs_ILP_vs_ILP_PS(self, beta, nm_id):
        df_ga = self.data_all[self.ga[nm_id]]
        df_ilp = self.data_all[self.ilp[nm_id]]
        df_ilp_ps = self.data_all[self.ilp_ps[nm_id]]
        list_arrival_rate = [0.01, 0.02, 0.03, 0.04]
        res = [[str(int(arrival_rate * 100))] for arrival_rate in list_arrival_rate]

        def get_res_success(_df):
            df_beta = _df.query(str('Beta == ' + str(beta)))
            i = 0
            for _arrival_rate in list_arrival_rate:
                df = df_beta.loc[df_beta['Arrival Rate'] == _arrival_rate]
                failure = df['Failure']
                success = df['Success']
                res[i].append(str(float(success) * 100.00 / float(failure + success)))
                i += 1

        def get_res_avg_bandwidth(_df):
            df_beta = _df.query(str('Beta == ' + str(beta)))
            i = 0
            for _arrival_rate in list_arrival_rate:
                df = df_beta.loc[df_beta['Arrival Rate'] == _arrival_rate]
                avg_bw = float(df['Average bandwidth'])
                res[i].append(str(avg_bw))
                i += 1

        file_name = "./wireless_sdn_results/Results_GA_vs_ILP_vs_PS_Beta_" + utils.demical_to_str(beta) + "_NM_" + str(nm_id) + tag + ".txt"
        fo = open(file_name, 'w')
        for _df in [df_ga, df_ilp, df_ilp_ps]:
            get_res_success(_df)
            get_res_avg_bandwidth(_df)
        for elem in res:
            fo.write(' '.join(elem) + '\n')
        fo.close()

    def get_results_Beta_all_in_one(self, nm_id, arrival_rate):
        df_ga = self.data_all[self.ga[nm_id]]
        df_ilp = self.data_all[self.ilp[nm_id]]
        df_ilp_ps = self.data_all[self.ilp_ps[nm_id]]
        list_beta = [0.0, 1.0]
        # list_beta = [0.0, 0.2, 0.4, 0.6]
        res_beta = [[str(beta)] for beta in list_beta]
        res_success_rate = [[] for _ in list_beta]
        res_avg_bandwidth = [[] for _ in list_beta]
        res_avg_interference = [[] for _ in list_beta]

        def get_res_success_rate(_df, _arrival_rate):
            df_arrival = _df.loc[_df['Arrival Rate'] == _arrival_rate]
            i = 0
            for beta in list_beta:
                df = df_arrival.query(str('Beta == ' + str(beta)))
                failure = float(df['Failure'])
                success = float(df['Success'])
                res_success_rate[i].append(str((success) * 100.00 / (failure + success)))
                i += 1

        def get_res_avg_bandwidth(_df, _arrival_rate):
            df_arrival = _df.loc[_df['Arrival Rate'] == _arrival_rate]
            i = 0
            for beta in list_beta:
                df = df_arrival.query(str('Beta == ' + str(beta)))
                avg_bw = float(df['Average bandwidth'])
                res_avg_bandwidth[i].append(str(avg_bw))
                i += 1

        def get_res_avg_interference(_df, _arrival_rate):
            df_arrival = _df.loc[_df['Arrival Rate'] == _arrival_rate]
            i = 0
            for beta in list_beta:
                df = df_arrival.query(str('Beta == ' + str(beta)))
                avg_intef = float(df['Average interference'])
                res_avg_interference[i].append(str(avg_intef))
                i += 1

        file_name = "./wireless_sdn_results/Results_Beta.txt"
        fo = open(file_name, 'w')
        for _df in [df_ga, df_ilp, df_ilp_ps]:
            get_res_success_rate(_df, arrival_rate)
            get_res_avg_bandwidth(_df, arrival_rate)
            get_res_avg_interference(_df, arrival_rate)
        for i in range(len(list_beta)):
            elem = res_beta[i] + res_avg_interference[i] + res_avg_bandwidth[i] + res_success_rate[i]
            fo.write(' '.join(elem) + '\n')
        fo.close()


process_result = ProcessResultsForPaper()

def go_1():
    for beta in [0.6]:
        for nm_id in [1, 2, 3]:
            process_result.get_results_GA_vs_ILP_vs_ILP_PS(beta, nm_id)

def go_2():
    process_result.get_results_Beta_all_in_one(2, 0.04)

# go_1()
go_2()

