# coding: utf-8
from __future__ import print_function
import networkx as nx
from deap import tools, base, creator
from multiprocessing import Pool
from wireless_sdn_tree_model_ga import TreeModelGA
from wireless_sdn_steiner_sph import SteinerSPH
import wireless_sdn_algorithm_core
from wireless_sdn_graph_model import ResourceModel
import copy
import random


i_global = 0


def fitness(chromosome, graph_model, list_request_bw,
            bw_info_dict, list_nodes, sw_init, number_nodes, of_table_info_dict, dict_interference_pair_info,
            dict_link_clique_id, dict_clique_id_residual_capacity, dict_clique_id_clique,
            obj_fun_parameters, load_balancing, sw_resource_balancing, min_max_clique_utilization_scheme):
    fit = get_fitness_bandwidth(chromosome, list_request_bw) * obj_fun_parameters[0]
    fit += get_fitness_openflow_resource(chromosome) * obj_fun_parameters[1]
    fit += get_fitness_group_resource(chromosome) * obj_fun_parameters[2]
    fit += get_fitness_interference(chromosome, list_request_bw, dict_interference_pair_info) * obj_fun_parameters[3]
    if load_balancing != 0 and min_max_clique_utilization_scheme != 0:
        fit += load_balancing * get_fitness_clique_utilization_max_min(
            chromosome, graph_model, list_request_bw, dict_clique_id_residual_capacity,
            dict_clique_id_clique, min_max_clique_utilization_scheme)
    if sw_resource_balancing != 0:
        fit += sw_resource_balancing * get_fitness_switch_resource_utilization_max_min(
            chromosome, sw_init, of_table_info_dict, number_nodes)
    fit *= get_fitness_cliques(chromosome, graph_model, list_request_bw, bw_info_dict,
                               dict_link_clique_id, dict_clique_id_residual_capacity, dict_clique_id_clique)
    fit *= get_fitness_openflow_hat(chromosome, list_nodes, of_table_info_dict)
    fit *= get_fitness_group_hat(chromosome, list_nodes, of_table_info_dict)
    return fit,


def get_fitness_openflow_resource(chromosome):
    resource = 0
    for tree_model in chromosome:
        resource += len(tree_model.T.nodes())
    return resource


def get_fitness_clique_utilization_max_min(chromosome, graph_model, list_request_bw,
                dict_clique_id_residual_capacity, dict_clique_id_clique, min_max_clique_utilization_scheme):
    cu_max = float('-inf')
    cu_min = float('inf')
    for clique_id, clique in dict_clique_id_clique.items():
        total_bw = 0
        j = 0
        for tree_model in chromosome:
            request_bw = list_request_bw[j]
            _links = tree_model.links
            j += 1
            n = 0
            for _link in _links:
                if _link in clique:
                    n += 1
            total_bw += n * request_bw
        cu_max = max(total_bw - dict_clique_id_residual_capacity[clique_id]
                     + graph_model.json_channels[1]['capacity'], cu_max)
        cu_min = min(total_bw - dict_clique_id_residual_capacity[clique_id]
                     + graph_model.json_channels[1]['capacity'], cu_min)
    if min_max_clique_utilization_scheme == 1:
        return cu_max
    else:
        return cu_max - cu_min


def get_fitness_switch_resource_utilization_max_min(chromosome, sw_init, of_table_info_dict, number_nodes):
    list_of_table_utilization = [sw_init - of_table_info_dict[node].openflow_entries_residu
                                 for node in range(1, number_nodes + 1)]
    for tree_model in chromosome:
        for node in tree_model.T.nodes():
            list_of_table_utilization[node - 1] += 1
    su_max = max(list_of_table_utilization)
    su_min = min(list_of_table_utilization)
    return su_max - su_min


def is_multicast_advantage(_tree_model, _node):
    exits = []
    exits_channel = []
    for dst in _tree_model.list_dst:
        path = nx.shortest_path(_tree_model.T, _tree_model.src, dst)
        if _node in path:
            i = path.index(_node)
            if i + 1 <= len(path) - 1:
                exits.append((_node, path[i + 1]))
                exits_channel.append(_tree_model.local_multi_link_info_dict[tuple(sorted([_node, path[i + 1]]))][1])
    if len(exits_channel) <= 1:
        return False
    for j in range(1, len(exits_channel)):
        if exits_channel[j] != exits_channel[0]:
            return False
    return True


def get_fitness_group_resource(chromosome):
    resource = 0
    for tree_model in chromosome:
        for node in tree_model.T.nodes():
            if len(tree_model.T[node]) >= 3:
                if not is_multicast_advantage(tree_model, node):
                    resource += 1
    return resource


def get_fitness_openflow_hat(chromosome, list_nodes, of_table_info_dict):
    result = 1
    of_table_l = {node: 0 for node in list_nodes}
    for tree_model in chromosome:
        for node in tree_model.T.nodes():
            '''
            Each node in the tree T,
            consumes one openflow table entry.
            '''
            of_table_l[node] += 1
    for node in list_nodes:
        if of_table_l[node] > of_table_info_dict[node].openflow_entries_residu:
            result += 10  # or, 100
    return result


def get_fitness_group_hat(chromosome, list_nodes, of_table_info_dict):
    result = 1
    of_table_m = {node: 0 for node in list_nodes}
    for tree_model in chromosome:
        for node in tree_model.T.nodes():
            if len(tree_model.T[node]) >= 3:
                if not is_multicast_advantage(tree_model, node):
                    of_table_m[node] += 1
    for node in list_nodes:
        if of_table_m[node] > of_table_info_dict[node].group_entries_residu:
            result += 10 # or, 100
    return result


def get_fitness_bandwidth(chromosome, list_request_bw):
    j = 0
    total_bw = 0
    for tree_model in chromosome:
        request_bw = list_request_bw[j]
        n = len(tree_model.links)
        j += 1
        total_bw += n * request_bw
    return total_bw


def get_fitness_interference(chromosome, list_request_bw, dict_interference_pair_info):
    j = 0
    total_interf = 0
    for tree_model in chromosome:
        request_bw = list_request_bw[j]
        for _link_id in tree_model.links:
            n_I = dict_interference_pair_info[_link_id].num_of_interference_pairs
            total_interf += n_I * request_bw
        j += 1
    return total_interf


def get_fitness_cliques_backup(chromosome, graph_model, list_request_bw, bw_info_dict):  # Equation 8
    result = 1
    cliques = graph_model.all_cliques
    for clique in cliques:
        total_bw = 0
        j = 0
        for tree_model in chromosome:
            request_bw = list_request_bw[j]
            _links = tree_model.links
            j += 1
            n = 0
            for _link in _links:
                if _link in clique:
                    n += 1
            total_bw += n * request_bw
        min_bw_residu = min([bw_info_dict[link_id].bw_residu for link_id in clique])
        if total_bw > min_bw_residu:
            result += 10  # or, 100
    return result


def get_fitness_cliques(chromosome, graph_model, list_request_bw, bw_info_dict,
                        dict_link_clique_id, dict_clique_id_residual_capacity, dict_clique_id_clique):  # Equation 8
    result = 1
    for clique_id, clique in dict_clique_id_clique.items():
        total_bw = 0
        j = 0
        for tree_model in chromosome:
            request_bw = list_request_bw[j]
            _links = tree_model.links
            j += 1
            n = 0
            for _link in _links:
                if _link in clique:
                    n += 1
            total_bw += n * request_bw
        if total_bw > dict_clique_id_residual_capacity[clique_id]:
            result += 10  # or, 100
    return result


def mutate_tree(chromosome, mutpb):
    # TODO: Higher mutate rate for links that have no available bandwidth !!!
    # That is, in cliques_not_satisfying_next
    for tree_model in chromosome:
        if random.random() >= mutpb:
            continue
        tree_model.mutate_one_link()
        del chromosome.fitness.values
    return chromosome,


def cx_two_trees((individual1, individual2),
                 dict_link_clique_id,
                 dict_clique_id_residual_capacity,
                 dict_clique_id_clique, requests, number_of_requests, transmission_int_link_key_dict,
                 cxpb, one_by_one_overload_avoidance_strategy):
    '''
    1. Determine tree_model_cx_3 and tree_model_cx_4 which contain common links between tree_model_1 and tree_model_2
    2. for tree_model_cx_3 and tree_model_cx_4, link disconnected parts of the graph
    '''
    if random.random() >= cxpb:
        return individual1, individual2

    pair_dict_clique_id_residual_capacity = [copy.deepcopy(dict_clique_id_residual_capacity),
                                             copy.deepcopy(dict_clique_id_residual_capacity)]

    pair_cliques_not_satisfying_next = [[], []]
    processing_order = range(number_of_requests)
    if one_by_one_overload_avoidance_strategy == 1:
        # This work of processing order could be offloaded to earlier stages.
        processing_order = map(lambda x: x[1],
                               sorted([(requests[k].request_bw, k) for k in range(number_of_requests)], reverse=True))
    elif one_by_one_overload_avoidance_strategy == 2:
        # This work of processing order could be offloaded to earlier stages.
        processing_order = map(lambda x: x[1],
                               sorted([(requests[k].request_bw, k) for k in range(number_of_requests)], reverse=False))
    elif one_by_one_overload_avoidance_strategy == 3:
        random.shuffle(processing_order)
    elif one_by_one_overload_avoidance_strategy == 0:
        pass

    def update_clique_residual_and_next_clique_violation(which, bw, tree_links, next_bw):
        if one_by_one_overload_avoidance_strategy == 0:
            return
        for _link in tree_links:
            clique_id_set = dict_link_clique_id[_link]
            for clique_id in clique_id_set:
                pair_dict_clique_id_residual_capacity[which][clique_id] -= bw
        for clique_id, residual in pair_dict_clique_id_residual_capacity[which].items():
            if residual < next_bw:
                pair_cliques_not_satisfying_next[which].append(clique_id)

    for j in range(number_of_requests):
        i = processing_order[j]
        bw = requests[i].request_bw

        tree_model_1 = individual1[i]
        tree_model_2 = individual2[i]
        links_common = [transmission_int_link_key_dict[k] for k in
                        tree_model_1.links.intersection(tree_model_2.links)]

        tree_model_cx_3 = copy.deepcopy(tree_model_1)
        tree_model_cx_4 = copy.deepcopy(tree_model_2)

        if j == 0:
            update_clique_residual_and_next_clique_violation(0, 0, set([]), bw)
            update_clique_residual_and_next_clique_violation(1, 0, set([]), bw)

        tree_model_cx_3.cliques_not_satisfying_next = pair_cliques_not_satisfying_next[0]
        tree_model_cx_4.cliques_not_satisfying_next = pair_cliques_not_satisfying_next[1]

        tree_model_cx_3.T = nx.Graph()
        for e in links_common:
            tree_model_cx_3.T.add_edge(*e, weight=tree_model_cx_3.G[e[0]][e[1]]["weight"])
        for node in [tree_model_cx_3.src] + tree_model_cx_3.list_dst:
            tree_model_cx_3.T.add_node(node)
        tree_model_cx_3.connect_several_disconnected_components()

        tree_model_cx_4.T = nx.Graph()
        for e in links_common:
            tree_model_cx_4.T.add_edge(*e, weight=tree_model_cx_4.G[e[0]][e[1]]["weight"])
        for node in [tree_model_cx_4.src] + tree_model_cx_4.list_dst:
            tree_model_cx_4.T.add_node(node)
        tree_model_cx_4.connect_several_disconnected_components()

        individual1[i] = tree_model_cx_3
        individual2[i] = tree_model_cx_4

        if j < number_of_requests - 1:
            next_bw = requests[processing_order[j + 1]].request_bw
            pair_cliques_not_satisfying_next = [[], []]
            update_clique_residual_and_next_clique_violation(0, bw, tree_model_cx_3.links, next_bw)
            update_clique_residual_and_next_clique_violation(1, bw, tree_model_cx_4.links, next_bw)

    del individual1.fitness.values, individual2.fitness.values
    return individual1, individual2


def get_tree_model(requests, graph_model, dict_link_id_link_cost,
                   number_of_requests, chapb,
                   use_multicast_advantage, one_by_one_overload_avoidance_strategy,
                   multiplier_factor, dynamic_link_cost_mode):
    global i_global
    req = requests[i_global]
    tree_model = TreeModelGA(graph_model)
    tree_model.req = req
    tree_model.request_id = req.request_id
    tree_model.src = req.src
    tree_model.list_dst = req.list_dst
    tree_model.use_multicast_advantage = use_multicast_advantage
    tree_model.one_by_one_overload_avoidance_strategy = one_by_one_overload_avoidance_strategy
    tree_model.multiplier_factor = multiplier_factor

    tree_model.dict_link_id_link_cost = copy.deepcopy(dict_link_id_link_cost)

    tree_model.chapb = chapb
    i_global += 1
    if i_global == number_of_requests:
        i_global = 0

    if dynamic_link_cost_mode:
        tree_model.create_random_sph_steiner_tree_from_dynamic_link_cost()
    else:
        tree_model.create_random_sph_steiner_tree_from_static_link_cost()

    tree_model.determine_links_vlinks()
    return tree_model


def init_link_costs(number_links_transmission, dict_interference_pair_info, obj_fun_parameters):
    dict_link_id_link_cost = {}
    for i in range(1, number_links_transmission + 1):
        n_I = dict_interference_pair_info[i].num_of_interference_pairs
        link_cost = float(obj_fun_parameters[0] + obj_fun_parameters[1] + obj_fun_parameters[3] * n_I)
        dict_link_id_link_cost[i] = link_cost
    return dict_link_id_link_cost


def main_with_static_link_cost(graph_model, requests, NGEN, IND_SIZE, CXPB, MUTPB, CHAPB,
         n_process=1, obj_fun_parameters=(1, 0.1, 0.1, 0.03),
         use_multicast_advantage=True, one_by_one_overload_avoidance_strategy=1, multiplier_factor=1.5,
         load_balancing=5, min_max_clique_utilization_scheme=2, sw_resource_balancing=15, sw_init=20000,
         dynamic_link_cost_mode=False, dict_link_id_link_cost=None):
    G = graph_model.G_int
    number_nodes = graph_model.number_nodes
    number_links_transmission = graph_model.number_links_transmission
    list_nodes = G.nodes()
    multi_link_info_dict = graph_model.multi_link_info_dict
    int_link_transmission_dict = graph_model.int_link_transmission_dict
    transmission_int_link_key_dict = graph_model.transmission_int_link_key_dict
    dict_interference_pair_info = graph_model.dict_interference_pair_info

    dict_link_clique_id = graph_model.dict_link_clique_id
    dict_clique_id_residual_capacity = graph_model.dict_clique_id_residual_capacity
    dict_clique_id_clique = graph_model.dict_clique_id_clique

    bw_info_dict = graph_model.bw_info_dict
    of_table_info_dict = graph_model.of_table_info_dict

    requests = requests
    number_of_requests = len(requests)
    list_request_bw = [request.request_bw for request in requests]

    local_multi_link_info_dict = {}

    if dynamic_link_cost_mode:
        dict_link_id_link_cost = dict_link_id_link_cost
    else:
        # ---------- IMPORTANT -----------
        dict_link_id_link_cost = init_link_costs(number_links_transmission, dict_interference_pair_info, obj_fun_parameters)
        for _key in G.edges():
            multi_link_info = multi_link_info_dict[_key]
            _link_id = min(list(multi_link_info.links_set), key=lambda link: dict_link_id_link_cost[link])
            _ch = multi_link_info.link_channel_dict[_link_id]
            local_multi_link_info_dict[_key] = (_link_id, _ch)
            G[_key[0]][_key[1]]["weight"] = dict_link_id_link_cost[_link_id]

    ngen, ind_size, cxpb, mutpb, chapb = NGEN, IND_SIZE, CXPB, MUTPB, CHAPB
    creator.create("FitnessMin", base.Fitness, weights=(-1,))
    creator.create("Individual", list, fitness=creator.FitnessMin)
    toolbox = base.Toolbox()
    toolbox.register("attribute", get_tree_model,
                     requests=requests,
                     graph_model=graph_model,
                     dict_link_id_link_cost=dict_link_id_link_cost,
                     number_of_requests=number_of_requests, chapb=chapb,
                     use_multicast_advantage=use_multicast_advantage,
                     one_by_one_overload_avoidance_strategy=one_by_one_overload_avoidance_strategy,
                     multiplier_factor=multiplier_factor,
                     dynamic_link_cost_mode=dynamic_link_cost_mode)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     toolbox.attribute, n=number_of_requests)  # Number of variables
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mate", cx_two_trees,
                     dict_link_clique_id=dict_link_clique_id,
                     dict_clique_id_residual_capacity=dict_clique_id_residual_capacity,
                     dict_clique_id_clique=dict_clique_id_clique,
                     requests=requests,
                     number_of_requests=number_of_requests,
                     transmission_int_link_key_dict=transmission_int_link_key_dict,
                     cxpb=cxpb,
                     one_by_one_overload_avoidance_strategy=one_by_one_overload_avoidance_strategy)  # CrossOver
    toolbox.register("mutate", mutate_tree, mutpb=mutpb)  # Mutate
    toolbox.register("select", tools.selTournament, tournsize=5)
    toolbox.register("evaluate", fitness, graph_model=graph_model,
                     list_request_bw=list_request_bw,
                     bw_info_dict=bw_info_dict, list_nodes=list_nodes,
                     sw_init=sw_init,
                     number_nodes=number_nodes,
                     of_table_info_dict=of_table_info_dict,
                     dict_interference_pair_info=dict_interference_pair_info,
                     dict_link_clique_id=dict_link_clique_id,
                     dict_clique_id_residual_capacity=dict_clique_id_residual_capacity,
                     dict_clique_id_clique=dict_clique_id_clique,
                     obj_fun_parameters=obj_fun_parameters,
                     load_balancing=load_balancing,
                     sw_resource_balancing=sw_resource_balancing,
                     min_max_clique_utilization_scheme=min_max_clique_utilization_scheme)  # Evaluate fitness
    if n_process >= 2:
        pool = Pool(n_process)
        toolbox.register("map", pool.map) # multi-processor, which works but doesn't seem to boost the computation time.

    population = toolbox.population(n=ind_size)
    halloffame = tools.HallOfFame(2)
    try:
        wireless_sdn_algorithm_core.myEaSimple(population, toolbox, cxpb, mutpb, ngen,
                                               halloffame=halloffame, verbose=True)
    except StopIteration:
        pass
    finally:
        pass

    mvp = halloffame[0]

    if get_fitness_group_hat(mvp, list_nodes, of_table_info_dict) > 1:
        return False, None, None, None
    
    if get_fitness_openflow_hat(mvp, list_nodes, of_table_info_dict) > 1:
        return False, None, None, None
    if get_fitness_cliques(mvp, graph_model, list_request_bw,
                           bw_info_dict, dict_link_clique_id,
                           dict_clique_id_residual_capacity, dict_clique_id_clique) > 1:
        return False, None, None, None

    for tree_model in mvp:
        tree_info = "["
        for _link_id in sorted(list(tree_model.links)):
            transmission_link = int_link_transmission_dict[_link_id]
            tree_info += "(" + str(transmission_link.src) + ", " + str(transmission_link.dst) + ", " \
                + transmission_link.color + "), "
        tree_info += "]"
        print("result for request ", str(tree_model.request_id), ": ", tree_info)

    _fitness_value = fitness(halloffame[0], graph_model, list_request_bw,
             bw_info_dict, list_nodes, sw_init, number_nodes, of_table_info_dict, dict_interference_pair_info,
             dict_link_clique_id, dict_clique_id_residual_capacity, dict_clique_id_clique,
             obj_fun_parameters, load_balancing, sw_resource_balancing, min_max_clique_utilization_scheme)

    resource_consume = ResourceModel(number_nodes=number_nodes,
                                     number_links_transmission=number_links_transmission)
    _i = 0
    for tree_model in mvp:
        for n in tree_model.T.nodes():
            resource_consume.dict_node_id_openflow_table_decrease[n] += 1
            if len(tree_model.T[n]) >= 3:
                if not is_multicast_advantage(tree_model, n):
                    resource_consume.dict_node_id_group_table_decrease[n] += 1
        bw = int(requests[_i].request_bw)
        for link_id in tree_model.links:
            resource_consume.total_bw_consumed += bw
            resource_consume.dict_link_id_total_bw_consumption[link_id] += bw
            resource_consume.total_interference_brought \
                += bw * dict_interference_pair_info[link_id].num_of_interference_pairs
        _i += 1

    return True, _fitness_value, resource_consume, mvp


class GeneticAlgorithmWithDynamicLinkCost(SteinerSPH):
    '''
    The differences of GA and SPH in terms of (prohibitive) dynamic link adjustment:
    1. GA adjusts cliques_not_satisfying_next with crossover. Meanwhile, SPH adjust cliques_not_satisfying_next directly with a tree model.
    2. GA updates dict_link_id_link_cost in a batch manner. By contrast, SPH updates dict_link_id_link_cost in a one by one manner.
    '''

    def __init__(self, graph_model, NGEN, IND_SIZE, CXPB,
                 MUTPB, CHAPB, use_multicast_advantage=True,
                 one_by_one_overload_avoidance_strategy=3,
                 multiplier_factor=1.5,
                 load_balancing=5,
                 min_max_clique_utilization_scheme=2,
                 sw_resource_balancing=15,
                 n_process=1, obj_fun_parameters=(1, 0.1, 0.1, 0.03), sw_init=20000,
                 K=2, power=2, threshold=20,
                 K_sw=3, power_sw=1.5, threshold_sw=30, power_else=1.0, power_sw_else=1.0):

        SteinerSPH.__init__(self, graph_model, obj_fun_parameters=obj_fun_parameters, K=K, power=power, threshold=threshold, sph_cost_scheme=0,
                            sw_init=sw_init, K_sw=K_sw, power_sw=power_sw, threshold_sw=threshold_sw,
                            do_nothing=0, power_else=power_else, power_sw_else=power_sw_else)

        self.NGEN = NGEN
        self.IND_SIZE = IND_SIZE
        self.CXPB = CXPB
        self.MUTPB = MUTPB
        self.CHAPB = CHAPB
        self.graph_model = graph_model
        self.n_process = n_process
        self.obj_fun_parameters = obj_fun_parameters
        self.use_multicast_advantage = use_multicast_advantage
        self.one_by_one_overload_avoidance_strategy = one_by_one_overload_avoidance_strategy
        self.multiplier_factor = multiplier_factor
        self.load_balancing = load_balancing
        self.min_max_clique_utilization_scheme = min_max_clique_utilization_scheme
        self.sw_resource_balancing = sw_resource_balancing
        self.sw_init = sw_init

        self.tree_model_base = TreeModelGA(graph_model)

        self.tree_model_base.use_multicast_advantage = True  # yeah, certainly. Pass the param here later.
        self.tree_model_base.one_by_one_overload_avoidance_strategy = 3  # of no use here.

        self.tree_model_base.multiplier_factor = multiplier_factor

        self.tree_model_base.switches_not_satisfying_next = []

        self.tree_model_base.obj_fun_parameters = obj_fun_parameters
        self.tree_model_base.init_link_costs()

        self.dict_link_id_link_cost_base = copy.deepcopy(self.tree_model_base.dict_link_id_link_cost)
        self.dict_link_id_link_cost = copy.deepcopy(self.dict_link_id_link_cost_base)

        self.do_nothing = 0

    def main_with_dynamic_link_cost(self, requests):
        return main_with_static_link_cost(
            self.graph_model, requests, self.NGEN, self.IND_SIZE, self.CXPB, self.MUTPB, self.CHAPB,
            n_process=self.n_process,
            obj_fun_parameters=self.obj_fun_parameters,
            use_multicast_advantage=self.use_multicast_advantage,
            one_by_one_overload_avoidance_strategy=self.one_by_one_overload_avoidance_strategy,
            multiplier_factor=self.multiplier_factor,
            load_balancing=self.load_balancing,
            min_max_clique_utilization_scheme=self.min_max_clique_utilization_scheme,
            sw_resource_balancing=self.sw_resource_balancing,
            sw_init=self.sw_init,
            dynamic_link_cost_mode=True,
            dict_link_id_link_cost=self.dict_link_id_link_cost)

    def update_link_cost_in_a_batch_manner(self, mvp):
        links_of_tree_models = set()
        nodes_of_tree_models = set()

        for tree_model in mvp:
            links_of_tree_models = links_of_tree_models.union(tree_model.links)
            nodes_of_tree_models = nodes_of_tree_models.union(tree_model.T.nodes())

        for clique_id, residual in self.graph_model.dict_clique_id_residual_capacity.items():
            self.hd[clique_id] = residual
        heap_cliques = sorted(self.hd.heap[:], reverse=False)
        # difference in utilization rate <= threshold
        if abs(float(heap_cliques[0][0] - heap_cliques[self.num_of_cliques - 1][0]) / float(
                self.graph_model.json_channels[1]['capacity']) * 100.0) <= self.threshold:
            self.K_max_cliques = []
            self.K_min_cliques = []
            self.normal_cliques = map(lambda x: x[1], heap_cliques[:])
        else:
            self.K_max_cliques = map(lambda x: x[1], heap_cliques[:self.K])
            self.K_min_cliques = map(lambda x: x[1], heap_cliques[-1 * self.K:])
            self.normal_cliques = map(lambda x: x[1], heap_cliques[self.K: (-1 * self.K)])

        heap_switches = []
        for node_id in range(1, self.graph_model.number_nodes + 1):
            heap_switches.append((self.graph_model.of_table_info_dict[node_id].openflow_entries_residu, node_id))
        heap_switches.sort(reverse=False)

        # difference in utilization rate <= threshold
        if abs(float(heap_switches[0][0] - heap_switches[self.graph_model.number_nodes - 1][0]) / float(
                self.graph_model.number_of_openflow_entries) * 100.0) <= self.threshold_sw:
            self.K_sw_max_switches = []
            self.K_sw_min_switches = []
        else:
            self.K_sw_max_switches = map(lambda x: x[1], heap_switches[:self.K_sw])
            self.K_sw_min_switches = map(lambda x: x[1], heap_switches[-1 * self.K_sw:])

        self.update_dynamic_link_cost(links_of_tree_models, nodes_of_tree_models)

