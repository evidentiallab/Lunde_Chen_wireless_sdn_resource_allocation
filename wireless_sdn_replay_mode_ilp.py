from __future__ import print_function
import copy
from wireless_sdn_ilp import ResourceAllocationILP, ResourceAllocationNoMulticastAdvantageILP
import wireless_sdn_replay_helper as replay
from wireless_sdn_requests import Task
import wireless_sdn_utils as utils
import time
import xlsxwriter
import csv


class AppReplayModeILP(object):
    def __init__(self, graph_model, req_tasks, nm_id, capacity_init, sw_init, sw_init_group, arrival_rate, tag,
                 path_split_ratio=1, obj_fun_parameters=(1, 0, 0, 0.1), use_multicast_advantage=True,
                 load_balancing=0, min_max_clique_utilization_scheme=1,
                 sw_resource_balancing=0):
        self.req_tasks = req_tasks
        self.time_max = req_tasks.time_max
        self.hd = req_tasks.hd
        self.nm_id = nm_id
        self.arrival_rate = arrival_rate
        self.graph_model_ilp = copy.deepcopy(graph_model)
        self.path_split_ratio = path_split_ratio
        self.obj_fun_parameters = obj_fun_parameters
        self.tag = tag
        self.capacity_init = capacity_init
        self.sw_init = sw_init
        self.sw_init_group = sw_init_group
        self.use_multicast_advantage = use_multicast_advantage
        self.load_balancing = load_balancing
        self.min_max_clique_utilization_scheme = min_max_clique_utilization_scheme
        self.sw_resource_balancing = sw_resource_balancing

    def start(self):
        if self.sw_init_group == -1:
            self.sw_init_group = self.graph_model_ilp.number_of_group_entries
        if self.sw_init == -1:
            self.sw_init = self.graph_model_ilp.number_of_openflow_entries
        _no_ma = ''
        if not self.use_multicast_advantage:
            _no_ma = '_no_ma'
        _str_init = '_cp_' + str(self.capacity_init)
        _str_load_balancing = '_lb_' + str(self.load_balancing)
        _str_min_max_clique_utilization_scheme = '_mm_' + str(self.min_max_clique_utilization_scheme)
        _str_switch_resource_balancing = '_sb_' + str(self.sw_resource_balancing)
        start_time = time.time()
        _str_path_split = ""
        if self.path_split_ratio <= 0.5:
            _str_path_split = "_ps_" + utils.demical_to_str(self.path_split_ratio)

        _head_name = "0_rep" + \
                     "_nm_" + str(self.nm_id) + "_rate_0" + utils.demical_to_str(self.arrival_rate, len_demical=2) + \
                     "_beta_" + utils.demical_to_str(self.obj_fun_parameters[3]) + _str_path_split + '_ilp' + self.tag + \
                     _str_init + _no_ma + _str_load_balancing + _str_min_max_clique_utilization_scheme + \
                     _str_switch_resource_balancing
        file_name = _head_name + ".txt"
        file_exel_name = _head_name + '_exel.xlsx'
        file_exel_bw_clique = _head_name + '_bw_clique_exel.xlsx'
        file_csv = _head_name + '.csv'

        workbook = xlsxwriter.Workbook(file_exel_name)
        worksheet = workbook.add_worksheet()

        workbook_bw_clique = xlsxwriter.Workbook(file_exel_bw_clique)
        worksheet_bw_clique = workbook_bw_clique.add_worksheet()

        fo_csv = open(file_csv, 'w')
        writer_csv = csv.writer(fo_csv)

        '''
        ATTENTION: clique_id is ranged from 2 to self.graph_model_ilp.clique_id
        '''
        first_row = ['UT', 'AcceptRate'] + map(str, range(2, self.graph_model_ilp.clique_id + 1)) + map(
            lambda x: 'SwConsumption' + str(x), range(1, self.graph_model_ilp.number_nodes + 1)) + map(
            lambda x: 'Group' + str(x), range(1, self.graph_model_ilp.number_nodes + 1))
        worksheet.write_row(0, 0, first_row)
        writer_csv.writerow(tuple(first_row))

        second_row = [-1, 100.00] + [0.00] * (self.graph_model_ilp.clique_id - 1 + self.graph_model_ilp.number_nodes * 2)
        worksheet.write_row(1, 0, second_row)
        writer_csv.writerow(tuple(second_row))

        worksheet_bw_clique.write_row(0, 0, ["UT", "REQ_BW", "BW_CONSUMED_THIS_MOMENT",
                                             "BW_RECOVERED_THIS_MOMENT", "BW_ACCUMULATED"]
                                      + map(str, range(2, self.graph_model_ilp.clique_id + 1)))
        _row = 1
        success = 0
        total = 0
        _bw_consumed_accumulated = 0

        while len(self.hd):
            (_time, (_t, task)) = self.hd.popitem()
            current_time = task.task_time
            if _time != current_time or _time != _t:
                print("NOT EQUAL")
                return

            if _time > self.time_max:
                break

            _row += 1

            _request_bw = 0
            _bw_consumed_this_moment = 0
            _bw_recovered_this_moment = 0

            if task.flag_new_requests:
                total += 1
                (pop_time, requests) = task.tuple_poptime_requests
                '''
                This is very important: path_split_ratio can be defined here.
                '''
                for req in requests:
                    req.path_split_ratio = self.path_split_ratio
                    _request_bw += req.request_bw

                if self.use_multicast_advantage:
                    resource_allocation_ilp = ResourceAllocationILP(
                        self.graph_model_ilp, obj_fun_parameters=self.obj_fun_parameters,
                        load_balancing=self.load_balancing,
                        min_max_clique_utilization_scheme=self.min_max_clique_utilization_scheme,
                        sw_resource_balancing=self.sw_resource_balancing, sw_init=self.sw_init)
                else:
                    resource_allocation_ilp = ResourceAllocationNoMulticastAdvantageILP(
                        self.graph_model_ilp, obj_fun_parameters=self.obj_fun_parameters,
                        load_balancing=self.load_balancing,
                        min_max_clique_utilization_scheme=self.min_max_clique_utilization_scheme,
                        sw_resource_balancing=self.sw_resource_balancing, sw_init=self.sw_init)

                flag_ilp = False
                try:
                    flag_ilp, res_ilp, resource_model_ilp = resource_allocation_ilp.main(
                        requests, time_limit=1200, mip_gap=0.01, flag_log=False)
                except Exception as e:
                    print("Problem Here : ", e.message)

                if flag_ilp:
                    _bw_consumed_this_moment += resource_model_ilp.total_bw_consumed

                (_, task_future) = self.hd.setdefault(pop_time, (pop_time, Task()))
                task_future.task_time = pop_time
                task_future.flag_expire_requests = True
                if flag_ilp:
                    task_future.expire_ilp.append(resource_model_ilp)

                fo = open(file_name, "a")
                elapsed_time = time.time() - start_time
                fo.write("Elapsed time: ILP " + str(elapsed_time) + "\n")
                fo.write("UT : " + str(current_time) + '\n')
                fo.write("ILP: " + str(flag_ilp) + '\n')
                if flag_ilp:
                    fo.write("ILP: " + str(res_ilp) + '\n')
                if flag_ilp:
                    fo.write("ILP: " + str(resource_model_ilp) + '\n')
                fo.write("-----------------------------\n")
                fo.close()

                if flag_ilp:
                    success += 1
                    replay.consume_resource(self.graph_model_ilp, resource_model_ilp)

            if task.flag_expire_requests:
                for resource_expire_ilp in task.expire_ilp:
                    replay.recover_resource(self.graph_model_ilp, resource_expire_ilp)
                    _bw_recovered_this_moment -= resource_expire_ilp.total_bw_consumed
            _bw_consumed_accumulated += _bw_recovered_this_moment + _bw_consumed_this_moment

            # node id starts from 1
            # clique id starts from 2
            arr = [current_time, 100.00 * float(success) / float(total)] + \
                map(lambda x: x[1], sorted([(_id, 100.00 * float(self.capacity_init - residu) / float(self.capacity_init))
                        for _id, residu in self.graph_model_ilp.dict_clique_id_residual_capacity.items()])) + \
                [100.00 * float(self.sw_init - self.graph_model_ilp.of_table_info_dict[_node_id].openflow_entries_residu) / float(self.sw_init)
                 for _node_id in range(1, self.graph_model_ilp.number_nodes + 1)] + \
                [self.sw_init_group - self.graph_model_ilp.of_table_info_dict[_node_id].group_entries_residu
                 for _node_id in range(1, self.graph_model_ilp.number_nodes + 1)]

            arr_bw_clique = [current_time, _request_bw, _bw_consumed_this_moment, _bw_recovered_this_moment, _bw_consumed_accumulated] + \
                map(lambda x: x[1], sorted([(_id, residu)
                        for _id, residu in self.graph_model_ilp.dict_clique_id_residual_capacity.items()]))

            worksheet.write_row(_row, 0, arr)
            writer_csv.writerow(tuple(arr))
            worksheet_bw_clique.write_row(_row - 1, 0, arr_bw_clique)
        workbook.close()
        workbook_bw_clique.close()
        fo_csv.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("nm_id", type=int, help="network model id")
    parser.add_argument("capacity_init", type=int, help="capacity init")
    parser.add_argument("arrival_rate", type=float, help="arrival rate")
    parser.add_argument("beta", type=float, help="beta")
    parser.add_argument('alpha2', type=float, help="alpha2")
    parser.add_argument('alpha3', type=float, help="alpha3")
    parser.add_argument('sw_openflow', type=int, help="sw_openflow")
    parser.add_argument('sw_group', type=int, help="sw_group")
    parser.add_argument('tag', type=str, help="tag")
    parser.add_argument("path_split_ratio", type=float, help="path_split_ratio")
    parser.add_argument('use_multicast_advantage', type=int, help="use_multicast_advantage")
    parser.add_argument('load_balancing', type=int,
                        help="load_balancing, or, gamma, as presented in the paper")
    parser.add_argument('min_max_clique_utilization_scheme', type=int, help="min_max_clique_utilization_scheme")
    parser.add_argument('sw_resource_balancing', type=int,
                        help="sw_resource_balancing parameter")
    args = parser.parse_args()
    nm_id = args.nm_id
    capacity_init = args.capacity_init
    arrival_rate = args.arrival_rate
    beta = args.beta
    alpha2 = args.alpha2
    alpha3 = args.alpha3
    sw_init = args.sw_openflow
    sw_init_group = args.sw_group
    tag = args.tag
    path_split_ratio = args.path_split_ratio
    use_multicast_advantage = (args.use_multicast_advantage != 0)
    load_balancing = args.load_balancing
    min_max_clique_utilization_scheme = args.min_max_clique_utilization_scheme
    sw_resource_balancing = args.sw_resource_balancing
    print("args: ", nm_id, " ", arrival_rate, " ", beta)
    gm = replay.load_graph_model("wireless_sdn_pickles/network_model_" + str(nm_id) + "/1")
    number_nodes = gm.number_nodes
    replay.reset_resource(gm, capacity_init, sw_init, sw_init_group)
    req_tasks = replay.load_req_tasks(
        "wireless_sdn_pickles/req_nodes_" + str(number_nodes)
        + "_rate_0" + utils.demical_to_str(arrival_rate, len_demical=2) + "/1")
    app = AppReplayModeILP(gm, req_tasks, nm_id, capacity_init, sw_init, sw_init_group, arrival_rate, tag,
                           path_split_ratio=path_split_ratio,
                           obj_fun_parameters=(1, alpha2, alpha3, beta),
                           use_multicast_advantage=use_multicast_advantage,
                           load_balancing=load_balancing,
                           min_max_clique_utilization_scheme=min_max_clique_utilization_scheme,
                           sw_resource_balancing=sw_resource_balancing)
    app.start()

