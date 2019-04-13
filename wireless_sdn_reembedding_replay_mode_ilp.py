from __future__ import print_function
import copy
from wireless_sdn_ilp import ResourceAllocationILP
from wireless_sdn_reembedding_ilp import ReEmbeddingILP
import wireless_sdn_replay_helper as replay
from wireless_sdn_requests import Task
import wireless_sdn_utils as utils
import time
import xlsxwriter
import csv


class AppReplayModeReembeddingILP(object):
    def __init__(self, graph_model, req_tasks, evolving_info, coefficient_reembedding, tag, nm_id=2, capacity_init=2, sw_init=2, sw_init_group=2,
                 path_split_ratio=1, obj_fun_parameters=(1, 0, 0, 0.1),
                 load_balancing=0, min_max_clique_utilization_scheme=1,
                 sw_resource_balancing=0):
        self.req_tasks = req_tasks
        self.evolving_info = evolving_info
        self.coefficient_reembedding = coefficient_reembedding

        self.time_max = req_tasks.time_max
        self.hd = req_tasks.hd
        self.nm_id = nm_id
        self.graph_model = copy.deepcopy(graph_model)
        self.path_split_ratio = path_split_ratio
        self.obj_fun_parameters = obj_fun_parameters
        self.tag = tag
        self.capacity_init = capacity_init
        self.sw_init = sw_init
        self.sw_init_group = sw_init_group
        self.load_balancing = load_balancing
        self.min_max_clique_utilization_scheme = min_max_clique_utilization_scheme
        self.sw_resource_balancing = sw_resource_balancing

    def start(self):
        if self.sw_init_group == -1:
            self.sw_init_group = self.graph_model.number_of_group_entries
        if self.sw_init == -1:
            self.sw_init = self.graph_model.number_of_openflow_entries
        start_time = time.time()

        _head_name = "0_rep" + '_EVOLVING' + self.tag + '_coeff_' + str(int(self.coefficient_reembedding))
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
        ATTENTION: clique_id is ranged from 2 to self.graph_model.clique_id
        '''
        first_row = ['UT', 'AcceptRate'] + map(str, range(2, self.graph_model.clique_id + 1)) + map(
            lambda x: 'SwConsumption' + str(x), range(1, self.graph_model.number_nodes + 1)) + map(
            lambda x: 'Group' + str(x), range(1, self.graph_model.number_nodes + 1)) \
            + ['count_reembedding_first_success', 'count_reembedding_second_success',
               'count_delta_increase_dst_nodes', 'count_delta_g_G_increase']
        worksheet.write_row(0, 0, first_row)
        writer_csv.writerow(tuple(first_row))

        second_row = [-1, 100.00] + [0.00] * (
            self.graph_model.clique_id - 1 + self.graph_model.number_nodes * 2) + [0, 0, 0, 0]
        worksheet.write_row(1, 0, second_row)
        writer_csv.writerow(tuple(second_row))

        worksheet_bw_clique.write_row(0, 0, ["UT", "REQ_BW", "BW_CONSUMED_THIS_MOMENT",
                                             "BW_RECOVERED_THIS_MOMENT", "BW_ACCUMULATED"]
                                      + map(str, range(2, self.graph_model.clique_id + 1)))
        _row = 1
        success = 0
        total = 0

        count_reembedding_first_success = 0
        count_reembedding_second_success = 0
        count_delta_increase_dst_nodes = 0
        count_delta_g_G_increase = 0

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

                '''
                ADD CODE HERE.
                '''
                flag_ilp = False

                if _time in self.evolving_info:

                    reembedding_ilp = ReEmbeddingILP(
                        self.graph_model, coefficient_reembedding=self.coefficient_reembedding, obj_fun_parameters=self.obj_fun_parameters,
                        load_balancing=self.load_balancing,
                        min_max_clique_utilization_scheme=self.min_max_clique_utilization_scheme,
                        sw_resource_balancing=self.sw_resource_balancing, sw_init=self.sw_init)

                    first_success, second_success = False, False

                    # try:
                    flag_ilp, first_success, second_success, res_ilp, resource_model_ilp, delta_increase_dst_nodes, delta_g_G_increase = reembedding_ilp.embed_and_then_reembed(
                        requests, self.evolving_info[_time], time_limit=1200, mip_gap=0.01, flag_log=False)
                    # except Exception as e:
                    #     print("Problem Here reembedding_ilp : ", e.message)

                    if first_success:
                        count_reembedding_first_success += 1
                    if second_success:
                        count_reembedding_second_success += 1
                        count_delta_increase_dst_nodes += delta_increase_dst_nodes
                        count_delta_g_G_increase += delta_g_G_increase

                        # TODO: add a member: REEMBEDDING SUCCESS WITHOUT BREAKING RATE

                else:
                    resource_allocation_ilp = ResourceAllocationILP(
                        self.graph_model, obj_fun_parameters=self.obj_fun_parameters,
                        load_balancing=self.load_balancing,
                        min_max_clique_utilization_scheme=self.min_max_clique_utilization_scheme,
                        sw_resource_balancing=self.sw_resource_balancing, sw_init=self.sw_init)

                    try:
                        flag_ilp, res_ilp, resource_model_ilp = resource_allocation_ilp.main(
                            requests, time_limit=1200, mip_gap=0.01, flag_log=False)
                    except Exception as e:
                        print("Problem Here resource_allocation_ilp : ", e.message)

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
                    replay.consume_resource(self.graph_model, resource_model_ilp)

            if task.flag_expire_requests:
                for resource_expire_ilp in task.expire_ilp:
                    replay.recover_resource(self.graph_model, resource_expire_ilp)
                    _bw_recovered_this_moment -= resource_expire_ilp.total_bw_consumed
            _bw_consumed_accumulated += _bw_recovered_this_moment + _bw_consumed_this_moment

            # node id starts from 1
            # clique id starts from 2
            arr = [current_time, 100.00 * float(success) / float(total)] + \
                map(lambda x: x[1], sorted([(_id, 100.00 * float(self.capacity_init - residu) / float(self.capacity_init))
                        for _id, residu in self.graph_model.dict_clique_id_residual_capacity.items()])) + \
                [100.00 * float(self.sw_init - self.graph_model.of_table_info_dict[_node_id].openflow_entries_residu) / float(self.sw_init)
                 for _node_id in range(1, self.graph_model.number_nodes + 1)] + \
                [self.sw_init_group - self.graph_model.of_table_info_dict[_node_id].group_entries_residu
                 for _node_id in range(1, self.graph_model.number_nodes + 1)] + \
                  [count_reembedding_first_success, count_reembedding_second_success,
                   count_delta_increase_dst_nodes, count_delta_g_G_increase]

            arr_bw_clique = [current_time, _request_bw, _bw_consumed_this_moment, _bw_recovered_this_moment, _bw_consumed_accumulated] + \
                map(lambda x: x[1], sorted([(_id, residu)
                        for _id, residu in self.graph_model.dict_clique_id_residual_capacity.items()]))

            worksheet.write_row(_row, 0, arr)
            writer_csv.writerow(tuple(arr))
            worksheet_bw_clique.write_row(_row - 1, 0, arr_bw_clique)
        workbook.close()
        workbook_bw_clique.close()
        fo_csv.close()


if __name__ == '__main__':
    graph_model = replay.load_graph_model("wireless_sdn_pickles/network_model_" + str(1) + "/1")
    req_tasks = replay.load_req_tasks('wireless_sdn_pickles/req_nodes_20_rate_002/1')
    evolving_info = replay.load_req_tasks('wireless_sdn_pickles/req_nodes_20_rate_002/1_evolving_add_nodes')
    coefficient_reembedding = 1000
    tag = 'NODES'
    rep = AppReplayModeReembeddingILP(graph_model, req_tasks, evolving_info, coefficient_reembedding, tag, nm_id=2, capacity_init=2, sw_init=2, sw_init_group=2,
                 path_split_ratio=1, obj_fun_parameters=(1, 0, 0, 0.1),
                 load_balancing=0, min_max_clique_utilization_scheme=1,
                 sw_resource_balancing=0)
    rep.start()


