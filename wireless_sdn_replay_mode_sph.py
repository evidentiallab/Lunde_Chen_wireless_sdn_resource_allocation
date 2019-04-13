from __future__ import print_function
import copy
from wireless_sdn_steiner_sph import SteinerSPH
import wireless_sdn_replay_helper as replay
from wireless_sdn_requests import Task
import wireless_sdn_utils as utils
import time
import xlsxwriter
import csv


def start_sph(graph_model, req_tasks, nm_id,
              capacity_init, sw_init, sw_init_group, arrival_rate, obj_fun_parameters=(1, 0, 0, 0.1),
              use_multicast_advantage=True,
              K=2, power=2, threshold=20, sph_cost_scheme=0,
              K_sw=3, power_sw=1.5, threshold_sw=30, do_nothing=0, power_else=1.0, power_sw_else=1.0,
              reverse_metric=0):
    _no_ma = ''
    if not use_multicast_advantage:
        _no_ma = '_no_ma'
    _str_init = '_cp_' + str(capacity_init)
    _str_sw_init = '_si_' + str(sw_init)
    _str_K = '_K_' + str(K)
    _str_power = '_pw_' + str(int(power * 10))
    _str_threshold = '_th_' + str(threshold)
    _str_sph_cost_scheme = '_sc_' + str(sph_cost_scheme)
    _str_K_sw = '_Ksw_' + str(K_sw)
    _str_power_sw = '_pwsw_' + str(int(power_sw * 10))
    _str_threshold_sw = '_thsw_' + str(threshold_sw)
    _str_do_nothing = '_dn_' + str(do_nothing)
    _str_power_else = '_pwel_' + str(int(power_else * 100))
    _str_power_sw_else = '_pwswel_' + str(int(power_sw_else * 100))
    graph_model_sph = copy.deepcopy(graph_model)
    if sw_init_group == -1:
        sw_init_group = graph_model.number_of_group_entries
    if sw_init == -1:
        sw_init = graph_model.number_of_openflow_entries
        _str_sw_init = ''
    hd = req_tasks.hd
    time_max = req_tasks.time_max
    start_time = time.time()
    _head_name = "0_rep" + \
                 "_nm_" + str(nm_id) + "_rate_0" + utils.demical_to_str(arrival_rate, len_demical=2) + \
                 "_beta_" + utils.demical_to_str(obj_fun_parameters[3]) + \
                 "_sph" + _str_sw_init + _str_init + _str_K + _str_power + _str_threshold + _no_ma + \
                 _str_K_sw + _str_power_sw + _str_threshold_sw + _str_do_nothing + _str_power_else + _str_power_sw_else
    if reverse_metric == 1:
        _head_name += '_rev'
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
    first_row = ['UT', 'AcceptRate'] + map(str, range(2, graph_model_sph.clique_id + 1)) + map(
            lambda x: 'SwConsumption' + str(x), range(1, graph_model_sph.number_nodes + 1)) + map(
            lambda x: 'Group' + str(x), range(1, graph_model_sph.number_nodes + 1))
    worksheet.write_row(0, 0, first_row)
    writer_csv.writerow(tuple(first_row))

    second_row = [-1, 100.00] + [0.00] * (graph_model_sph.clique_id - 1 + graph_model_sph.number_nodes * 2)
    worksheet.write_row(1, 0, second_row)
    writer_csv.writerow(tuple(second_row))

    worksheet_bw_clique.write_row(0, 0, ["UT", "REQ_BW", "BW_CONSUMED_THIS_MOMENT", "BW_RECOVERED_THIS_MOMENT",
                                         "BW_ACCUMULATED"] + map(str, range(2, graph_model_sph.clique_id + 1)))
    _row = 1
    success = 0
    total = 0
    _bw_consumed_accumulated = 0

    steiner_sph = SteinerSPH(graph_model=graph_model_sph, obj_fun_parameters=obj_fun_parameters,
                             K=K, power=power, threshold=threshold, sph_cost_scheme=sph_cost_scheme,
                             sw_init=sw_init, K_sw=K_sw, power_sw=power_sw,
                             threshold_sw=threshold_sw, do_nothing=do_nothing, power_else=power_else, power_sw_else=power_sw_else,
                             reverse_metric=reverse_metric)
    while len(hd):
        (_time, (_t, task)) = hd.popitem()
        current_time = task.task_time
        if _time != current_time or _time != _t:
            print("ERROR: NOT EQUAL")
            return

        if _time > time_max:
            break

        _row += 1
        _request_bw = 0
        _bw_consumed_this_moment = 0
        _bw_recovered_this_moment = 0

        if task.flag_new_requests:
            total += 1
            (pop_time, requests) = task.tuple_poptime_requests

            for req in requests:
                req.path_split_ratio = 1
                _request_bw += req.request_bw

            flag_sph = False
            resource_model_sph = None
            # try:
            flag_sph, resource_model_sph = \
                steiner_sph.main(requests)
            # except Exception as e:
            #     print("Error Replay SPH, Problem Here : ", e.message)

            if flag_sph:
                _bw_consumed_this_moment += resource_model_sph.total_bw_consumed

            (_, task_future) = hd.setdefault(pop_time, (pop_time, Task()))
            task_future.task_time = pop_time
            task_future.flag_expire_requests = True
            if flag_sph:
                task_future.expire_sph.append(resource_model_sph)

            fo = open(file_name, "a")
            elapsed_time = time.time() - start_time
            fo.write("Elapsed time: SPH " + str(elapsed_time) + "\n")
            fo.write("UT : " + str(current_time) + '\n')
            fo.write("SPH : " + str(flag_sph) + '\n')
            if flag_sph:
                fo.write("SPH : " + str(resource_model_sph) + '\n')
            fo.write("-----------------------------\n")
            fo.close()
            if flag_sph:
                success += 1
                replay.consume_resource(graph_model_sph, resource_model_sph)

        if task.flag_expire_requests:
            for resource_expire_sph in task.expire_sph:
                replay.recover_resource(graph_model_sph, resource_expire_sph)
                _bw_recovered_this_moment -= resource_expire_sph.total_bw_consumed
        _bw_consumed_accumulated += _bw_recovered_this_moment + _bw_consumed_this_moment

        arr = [current_time, 100.00 * float(success) / float(total)] + \
              map(lambda x: x[1], sorted([(_id, 100.00 * float(capacity_init - residu) / float(capacity_init))
                      for _id, residu in graph_model_sph.dict_clique_id_residual_capacity.items()])) + \
              [100.00 * float(
                sw_init - graph_model_sph.of_table_info_dict[_node_id].openflow_entries_residu) / float(
                sw_init) for _node_id in range(1, graph_model_sph.number_nodes + 1)] + \
              [sw_init_group - graph_model_sph.of_table_info_dict[_node_id].group_entries_residu
                for _node_id in range(1, graph_model_sph.number_nodes + 1)]
        arr_bw_clique = [current_time, _request_bw, _bw_consumed_this_moment, _bw_recovered_this_moment,
                         _bw_consumed_accumulated] + map(lambda x: x[1], sorted([(_id, residu) for _id, residu in
                         graph_model_sph.dict_clique_id_residual_capacity.items()]))

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
    parser.add_argument('use_multicast_advantage', type=int, help="use_multicast_advantage")
    parser.add_argument('K', type=int, help="K")
    parser.add_argument('power', type=float, help="power")
    parser.add_argument('threshold', type=int, help="threshold")
    parser.add_argument('sph_cost_scheme', type=int, help="sph_cost_scheme")
    parser.add_argument('K_sw', type=int, help="K_sw")
    parser.add_argument('power_sw', type=float, help="power_sw")
    parser.add_argument('threshold_sw', type=int, help="threshold_sw")
    parser.add_argument('do_nothing', type=int, help="do_nothing")
    parser.add_argument('power_else', type=float, help="power_else")
    parser.add_argument('power_sw_else', type=float, help="power_sw_else")
    parser.add_argument('reverse_metric', type=int, help="reverse_metric")
    args = parser.parse_args()
    nm_id = args.nm_id
    capacity_init = args.capacity_init
    arrival_rate = args.arrival_rate
    beta = args.beta
    alpha2 = args.alpha2
    alpha3 = args.alpha3
    sw_init = args.sw_openflow
    sw_init_group = args.sw_group
    use_multicast_advantage = (args.use_multicast_advantage != 0)
    K = args.K
    power = args.power
    threshold = args.threshold
    sph_cost_scheme = args.sph_cost_scheme
    K_sw = args.K_sw
    power_sw = args.power_sw
    threshold_sw = args.threshold_sw
    do_nothing = args.do_nothing
    power_else = args.power_else
    power_sw_else = args.power_sw_else
    reverse_metric = args.reverse_metric
    print("args: ", nm_id, " ", arrival_rate, " ", beta)
    gm = replay.load_graph_model("wireless_sdn_pickles/network_model_" + str(nm_id) + "/1")
    number_nodes = gm.number_nodes
    replay.reset_resource(gm, capacity_init, sw_init, sw_init_group)
    req_tasks = replay.load_req_tasks(
        "wireless_sdn_pickles/req_nodes_" + str(number_nodes)
        + "_rate_0" + utils.demical_to_str(arrival_rate, len_demical=2) + "/1")
    start_sph(gm, req_tasks, nm_id, capacity_init, sw_init, sw_init_group, arrival_rate,
              obj_fun_parameters=(1, alpha2, alpha3, beta),
              use_multicast_advantage=use_multicast_advantage,
              K=K, power=power, threshold=threshold,
              sph_cost_scheme=sph_cost_scheme,
              K_sw=K_sw, power_sw=power_sw, threshold_sw=threshold_sw,
              do_nothing=do_nothing, power_else=power_else, power_sw_else=power_sw_else, reverse_metric=reverse_metric)
