from __future__ import print_function
import copy
from wireless_sdn_ga import GeneticAlgorithmWithDynamicLinkCost
import wireless_sdn_replay_helper as replay
from wireless_sdn_requests import Task
import wireless_sdn_utils as utils
import time
import xlsxwriter
import csv

def start_ga(graph_model, req_tasks, nm_id,
             capacity_init, sw_init, sw_init_group, arrival_rate, num_population,
             num_generation, tag, prob_cx, prob_mt,
             prob_ch, obj_fun_parameters=(1, 0, 0, 0.1),
             use_multicast_advantage=True, one_by_one_overload_avoidance_strategy=0,
             multiplier_factor=1.5,
             load_balancing=0,
             min_max_clique_utilization_scheme=1,
             sw_resource_balancing=0,
             K=2, power=2, threshold=20,
             K_sw=3, power_sw=1.5, threshold_sw=30,
             power_else=1.0, power_sw_else=1.0):

    _no_ma = ''
    if not use_multicast_advantage:
        _no_ma = '_no_ma'
    _str_init = '_cp_' + str(capacity_init)
    _str_sw_init = '_si_' + str(sw_init)
    _str_strategy = '_str_' + str(one_by_one_overload_avoidance_strategy)
    _str_load_balancing = '_lb_' + str(load_balancing)
    _str_switch_resource_balancing = '_sb_' + str(sw_resource_balancing)
    _str_min_max_clique_utilization_scheme = '_mm_' + str(min_max_clique_utilization_scheme)
    _str_threshold = '_th_' + str(threshold)
    _str_threshold_sw = '_thsw_' + str(threshold_sw)
    graph_model_ga = copy.deepcopy(graph_model)
    if sw_init_group == -1:
        sw_init_group = graph_model_ga.number_of_group_entries
    if sw_init == -1:
        sw_init = graph_model_ga.number_of_openflow_entries
        _str_sw_init = ''
    hd = req_tasks.hd
    time_max = req_tasks.time_max
    start_time = time.time()

    _head_name = "0_rep" + \
                 "_nm_" + str(nm_id) + "_rate_0" + utils.demical_to_str(arrival_rate, len_demical=2) + \
                 "_beta_" + utils.demical_to_str(obj_fun_parameters[3]) + '_np_' + \
                 str(num_population) + '_ng_' + str(num_generation) + "_ga" + tag + \
                 _str_init + _no_ma + _str_load_balancing + \
                 _str_min_max_clique_utilization_scheme + \
                 _str_switch_resource_balancing + _str_threshold + _str_threshold_sw
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
    ATTENTION: clique_id is ranged from 2 to self.graph_model_ga.clique_id
    '''
    first_row = ['UT', 'AcceptRate'] + map(str, range(2, graph_model_ga.clique_id + 1)) + map(
            lambda x: 'SwConsumption' + str(x), range(1, graph_model_ga.number_nodes + 1)) + map(
            lambda x: 'Group' + str(x), range(1, graph_model_ga.number_nodes + 1))
    worksheet.write_row(0, 0, first_row)
    writer_csv.writerow(tuple(first_row))

    second_row = [-1, 100.00] + [0.00] * (graph_model_ga.clique_id - 1 + graph_model_ga.number_nodes * 2)
    worksheet.write_row(1, 0, second_row)
    writer_csv.writerow(tuple(second_row))

    worksheet_bw_clique.write_row(0, 0, ["UT", "REQ_BW", "BW_CONSUMED_THIS_MOMENT", "BW_RECOVERED_THIS_MOMENT",
                                         "BW_ACCUMULATED"]
                                  + map(str, range(2, graph_model_ga.clique_id + 1)))
    _row = 1
    success = 0
    total = 0
    _bw_consumed_accumulated = 0

    ga = GeneticAlgorithmWithDynamicLinkCost(
        graph_model_ga,
        NGEN=num_generation, IND_SIZE=num_population, CXPB=prob_cx,
        MUTPB=prob_mt, CHAPB=prob_ch,
        use_multicast_advantage=use_multicast_advantage,
        one_by_one_overload_avoidance_strategy=one_by_one_overload_avoidance_strategy,
        multiplier_factor=multiplier_factor,
        load_balancing=load_balancing,
        min_max_clique_utilization_scheme=min_max_clique_utilization_scheme,
        sw_resource_balancing=sw_resource_balancing,
        n_process=1,
        obj_fun_parameters=obj_fun_parameters,
        sw_init=sw_init,
        K=K, power=power, threshold=threshold,
        K_sw=K_sw, power_sw=power_sw, threshold_sw=threshold_sw,
        power_else=power_else, power_sw_else=power_sw_else)

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

            flag_ga = False
            resource_model_ga = None
            mvp = None

            # try:
            flag_ga, res_ga, resource_model_ga, mvp = ga.main_with_dynamic_link_cost(requests)
            # except Exception as e:
            #     print("Error Replay GA, Problem Here : ", e.message)

            if flag_ga:
                _bw_consumed_this_moment += resource_model_ga.total_bw_consumed

            (_, task_future) = hd.setdefault(pop_time, (pop_time, Task()))
            task_future.task_time = pop_time
            task_future.flag_expire_requests = True
            if flag_ga:
                task_future.expire_ga.append(resource_model_ga)

            fo = open(file_name, "a")
            elapsed_time = time.time() - start_time
            fo.write("Elapsed time: GA " + str(elapsed_time) + "\n")
            fo.write("UT : " + str(current_time) + '\n')
            fo.write("GA : " + str(flag_ga) + '\n')
            if flag_ga:
                fo.write("GA : " + str(res_ga) + '\n')
            if flag_ga:
                fo.write("GA : " + str(resource_model_ga) + '\n')
            fo.write("-----------------------------\n")
            fo.close()
            if flag_ga:
                success += 1
                replay.consume_resource(graph_model_ga, resource_model_ga)
                ga.update_link_cost_in_a_batch_manner(mvp)  # ---- VERY IMPORTANT ----

        if task.flag_expire_requests:
            for resource_expire_ga in task.expire_ga:
                replay.recover_resource(graph_model_ga, resource_expire_ga)
                _bw_recovered_this_moment -= resource_expire_ga.total_bw_consumed
        _bw_consumed_accumulated += _bw_recovered_this_moment + _bw_consumed_this_moment

        arr = [current_time, 100.00 * float(success) / float(total)] + \
              map(lambda x: x[1], sorted([(_id, 100.00 * float(capacity_init - residu) / float(capacity_init))
                      for _id, residu in graph_model_ga.dict_clique_id_residual_capacity.items()])) + \
              [100.00 * float(
                  sw_init - graph_model_ga.of_table_info_dict[_node_id].openflow_entries_residu) / float(
                  sw_init) for _node_id in range(1, graph_model_ga.number_nodes + 1)] + \
              [sw_init_group - graph_model_ga.of_table_info_dict[_node_id].group_entries_residu
               for _node_id in range(1, graph_model_ga.number_nodes + 1)]
        arr_bw_clique = [current_time, _request_bw, _bw_consumed_this_moment, _bw_recovered_this_moment,
                         _bw_consumed_accumulated] + map(lambda x: x[1], sorted([(_id, residu) for _id, residu in
                         graph_model_ga.dict_clique_id_residual_capacity.items()]))
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
    parser.add_argument('num_population', type=int, help="num_population")
    parser.add_argument('num_generation', type=int, help="num_generation")
    parser.add_argument('tag', type=str, help="tag")
    parser.add_argument('prob_cx', type=float, help="prob_cx")
    parser.add_argument('prob_mt', type=float, help="prob_mt")
    parser.add_argument('prob_ch', type=float, help="prob_ch")
    parser.add_argument('use_multicast_advantage', type=int, help="use_multicast_advantage")
    parser.add_argument('one_by_one_overload_avoidance_strategy', type=int,
                        help="one_by_one_overload_avoidance_strategy")
    parser.add_argument('multiplier_factor', type=float, help="multiplier_factor")
    parser.add_argument('load_balancing', type=int,
                        help="load_balancing, or, gamma, as presented in the paper")
    parser.add_argument('min_max_clique_utilization_scheme', type=int, help="min_max_clique_utilization_scheme")
    parser.add_argument('sw_resource_balancing', type=int, help="sw_resource_balancing")
    parser.add_argument('K', type=int, help="K")
    parser.add_argument('power', type=float, help="power")
    parser.add_argument('threshold', type=int, help="threshold")
    parser.add_argument('K_sw', type=int, help="K_sw")
    parser.add_argument('power_sw', type=float, help="power_sw")
    parser.add_argument('threshold_sw', type=int, help="threshold_sw")
    parser.add_argument('power_else', type=float, help="power_else")
    parser.add_argument('power_sw_else', type=float, help="power_sw_else")
    args = parser.parse_args()
    nm_id = args.nm_id
    capacity_init = args.capacity_init
    arrival_rate = args.arrival_rate
    beta = args.beta
    alpha2 = args.alpha2
    alpha3 = args.alpha3
    sw_init = args.sw_openflow
    sw_init_group = args.sw_group
    num_population = args.num_population
    num_generation = args.num_generation
    tag = args.tag
    prob_cx = args.prob_cx
    prob_mt = args.prob_mt
    prob_ch = args.prob_ch
    use_multicast_advantage = (args.use_multicast_advantage != 0)
    one_by_one_overload_avoidance_strategy = args.one_by_one_overload_avoidance_strategy
    multiplier_factor = args.multiplier_factor
    load_balancing = args.load_balancing
    min_max_clique_utilization_scheme = args.min_max_clique_utilization_scheme
    sw_resource_balancing = args.sw_resource_balancing
    K = args.K
    power = args.power
    threshold = args.threshold
    K_sw = args.K_sw
    power_sw = args.power_sw
    threshold_sw = args.threshold_sw
    power_else = args.power_else
    power_sw_else = args.power_sw_else

    gm = replay.load_graph_model("wireless_sdn_pickles/network_model_" + str(nm_id) + "/1")
    number_nodes = gm.number_nodes
    replay.reset_resource(gm, capacity_init, sw_init, sw_init_group)
    req_tasks = replay.load_req_tasks(
        "wireless_sdn_pickles/req_nodes_" + str(number_nodes)
        + "_rate_0" + utils.demical_to_str(arrival_rate, len_demical=2) + "/1")
    start_ga(gm, req_tasks, nm_id, capacity_init, sw_init, sw_init_group, arrival_rate,
             num_population, num_generation, tag, prob_cx, prob_mt, prob_ch,
             obj_fun_parameters=(1, alpha2, alpha3, beta),
             use_multicast_advantage=use_multicast_advantage,
             one_by_one_overload_avoidance_strategy=one_by_one_overload_avoidance_strategy,
             multiplier_factor=multiplier_factor,
             load_balancing=load_balancing,
             min_max_clique_utilization_scheme=min_max_clique_utilization_scheme,
             sw_resource_balancing=sw_resource_balancing,
             K=K, power=power, threshold=threshold,
             K_sw=K_sw, power_sw=power_sw, threshold_sw=threshold_sw,
             power_else=power_else, power_sw_else=power_sw_else)

