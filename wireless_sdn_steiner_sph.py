# coding: utf-8
from __future__ import print_function
from wireless_sdn_graph_model import ResourceModel
from wireless_sdn_tree_model_base import TreeModelBase
from wireless_sdn_heapdict import heapdict
import wireless_sdn_utils
import networkx as nx
import copy


class TreeModelSPH(TreeModelBase):
    def __init__(self, graph_model, obj_fun_parameters):
        TreeModelBase.__init__(self, graph_model)

        self.use_multicast_advantage = True   # yeah, certainly. Pass the param here later.
        self.one_by_one_overload_avoidance_strategy = 3  # of no use here.
        self.multiplier_factor = 1

        self.switches_not_satisfying_next = []

        self.obj_fun_parameters = obj_fun_parameters

    def obtain_sph_steiner_tree_result_from_new_link_cost(self):
        for clique_id in self.cliques_not_satisfying_next:
            clique = self.dict_clique_id_clique[clique_id]
            for _link_id in clique:
                self.dict_link_id_link_cost[_link_id] *= 50

        for node in self.switches_not_satisfying_next:
            for n in self.G[node].keys():
                _key = tuple(sorted((node, n)))
                for _link_id in self.graph_model.multi_link_info_dict[_key].links_set:
                    self.dict_link_id_link_cost[_link_id] *= 50

        for _key in self.G.edges():
            multi_link_info = self.multi_link_info_dict[_key]
            # ---------- Very Important ----------- #
            _link_id = min(list(multi_link_info.links_set), key=lambda link: self.dict_link_id_link_cost[link])
            _ch = multi_link_info.link_channel_dict[_link_id]
            self.local_multi_link_info_dict[_key] = (_link_id, _ch)
            self.G[_key[0]][_key[1]]["weight"] = self.dict_link_id_link_cost[_link_id]
        z = [self.src] + self.list_dst
        steiner_edges = wireless_sdn_utils.sph_steiner_dijkstra(self.G, z)[0]
        for e in steiner_edges:
            self.T.add_edge(*e, weight=self.G[e[0]][e[1]]["weight"])
        self.determine_links_vlinks()


class SteinerSPH(object):
    def __init__(self, graph_model, obj_fun_parameters, K=2, power=2, threshold=20, sph_cost_scheme=0,
                 sw_init=20000, K_sw=2, power_sw=1.5, threshold_sw=100, do_nothing=0, power_else=1.0,
                 power_sw_else=1.0, reverse_metric=0):

        self.graph_model = graph_model
        self.obj_fun_parameters = obj_fun_parameters
        self.tree_model_base = TreeModelSPH(graph_model, obj_fun_parameters)
        self.tree_model_base.init_link_costs()
        self.dict_link_id_link_cost_base = copy.deepcopy(self.tree_model_base.dict_link_id_link_cost)
        self.dict_link_id_link_cost = copy.deepcopy(self.dict_link_id_link_cost_base)
        self.K = K
        self.power = float(power)
        self.threshold = threshold
        self.hd = heapdict()
        self.num_of_cliques = len(self.graph_model.dict_clique_id_clique)

        self.K_max_cliques = []
        self.K_min_cliques = []
        self.normal_cliques = []  # of no use now
        self.sph_cost_scheme = sph_cost_scheme

        self.K_sw_max_switches = []
        self.K_sw_min_switches = []

        self.sw_init = sw_init
        self.K_sw = K_sw
        self.power_sw = power_sw
        self.threshold_sw = threshold_sw

        self.copy_dict_clique_id_residual_capacity = None
        self.cliques_not_satisfying_next = []

        self.copy_of_table_info_dict = None
        self.switches_not_satisfying_next = []

        self.do_nothing = do_nothing

        self.power_else = power_else
        self.power_sw_else = power_sw_else

        self.reverse_metric = reverse_metric

    def is_multicast_advantage(self, _tree_model, _node):
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

    def update_switch_entries_residual_and_next_switch_violation(self, tree_nodes):
        self.switches_not_satisfying_next = []
        heap = []

        for node_id in tree_nodes:
            self.copy_of_table_info_dict[node_id].openflow_entries_residu -= 1

        for node_id in range(1, self.graph_model.number_nodes + 1):
            if self.copy_of_table_info_dict[node_id].openflow_entries_residu <= 0:
                self.switches_not_satisfying_next.append(node_id)
            heap.append((self.copy_of_table_info_dict[node_id].openflow_entries_residu, node_id))
        heap.sort(reverse=False)

        # difference in utilization rate <= threshold
        if abs(float(heap[0][0] - heap[self.graph_model.number_nodes - 1][0]) / float(
                self.graph_model.number_of_openflow_entries) * 100.0) <= self.threshold_sw:
            self.K_sw_max_switches = []
            self.K_sw_min_switches = []
        else:
            self.K_sw_max_switches = map(lambda x: x[1], heap[:self.K_sw])
            self.K_sw_min_switches = map(lambda x: x[1], heap[-1 * self.K_sw:])

    def update_clique_residual_and_next_clique_violation(self, bw, tree_links, next_bw):
        self.cliques_not_satisfying_next = []

        for _link in tree_links:
            clique_id_set = self.graph_model.dict_link_clique_id[_link]
            for _clique_id in clique_id_set:
                self.copy_dict_clique_id_residual_capacity[_clique_id] -= bw
        for clique_id, residual in self.copy_dict_clique_id_residual_capacity.items():
            if residual < next_bw:
                self.cliques_not_satisfying_next.append(clique_id)
        for clique_id, residual in self.copy_dict_clique_id_residual_capacity.items():
            self.hd[clique_id] = residual
        heap = sorted(self.hd.heap[:], reverse=False)
        # difference in utilization rate <= threshold
        if abs(float(heap[0][0] - heap[self.num_of_cliques - 1][0]) / float(
                self.graph_model.json_channels[1]['capacity']) * 100.0) <= self.threshold:
            self.K_max_cliques = []
            self.K_min_cliques = []
            self.normal_cliques = map(lambda x: x[1], heap[:])
        else:
            self.K_max_cliques = map(lambda x: x[1], heap[:self.K])
            self.K_min_cliques = map(lambda x: x[1], heap[-1 * self.K:])
            self.normal_cliques = map(lambda x: x[1], heap[self.K: (-1 * self.K)])

    def main(self, requests):
        self.copy_dict_clique_id_residual_capacity = copy.deepcopy(self.graph_model.dict_clique_id_residual_capacity)
        self.copy_of_table_info_dict = copy.deepcopy(self.graph_model.of_table_info_dict)

        flag_success = True
        resource_consume = ResourceModel(number_nodes=self.graph_model.number_nodes,
                                         number_links_transmission=self.graph_model.number_links_transmission)
        requests.sort(key=lambda x: x.request_bw, reverse=True)
        number_of_requests = len(requests)
        _i = 0
        for req in requests:
            tree_model = copy.deepcopy(self.tree_model_base)
            tree_model.req = req
            tree_model.src = req.src
            tree_model.list_dst = req.list_dst
            tree_model.request_id = req.request_id
            tree_model.graph_model = self.graph_model
            bw = int(requests[_i].request_bw)

            if _i == 0:
                self.update_clique_residual_and_next_clique_violation(0, set([]), bw)
                self.update_switch_entries_residual_and_next_switch_violation([])

            # ---------- VERY IMPORTANT ------------ #
            tree_model.dict_link_id_link_cost = copy.deepcopy(self.dict_link_id_link_cost)

            tree_model.cliques_not_satisfying_next = self.cliques_not_satisfying_next
            tree_model.switches_not_satisfying_next = self.switches_not_satisfying_next

            tree_model.obtain_sph_steiner_tree_result_from_new_link_cost()

            for n in tree_model.T.nodes():
                resource_consume.dict_node_id_openflow_table_decrease[n] += 1
                if len(tree_model.T[n]) >= 3:
                    if not self.is_multicast_advantage(tree_model, n):
                        resource_consume.dict_node_id_group_table_decrease[n] += 1
            for link_id in tree_model.links:
                resource_consume.total_bw_consumed += bw
                resource_consume.dict_link_id_total_bw_consumption[link_id] += bw
                resource_consume.total_interference_brought += bw * \
                    tree_model.dict_interference_pair_info[link_id].num_of_interference_pairs

            for clique_id, clique in self.graph_model.dict_clique_id_clique.items():
                total_bw = 0
                n = 0
                for link_id in tree_model.links:
                    if link_id in clique:
                        n += 1
                total_bw += n * bw
                if total_bw > self.copy_dict_clique_id_residual_capacity[clique_id]:
                    flag_success = False
                    break

            for node_id in range(1, self.graph_model.number_nodes + 1):
                if self.copy_of_table_info_dict[node_id].openflow_entries_residu == 0:
                    if node_id in tree_model.T.nodes():
                        flag_success = False
                        break

            if flag_success:
                if self.reverse_metric:
                    self.update_reverse_link_cost()
                else:
                    self.update_dynamic_link_cost(tree_model.links, tree_model.T.nodes())
            else:
                break

            if _i < number_of_requests - 1:
                next_bw = requests[_i + 1].request_bw
                self.update_clique_residual_and_next_clique_violation(bw, tree_model.links, next_bw)
                self.update_switch_entries_residual_and_next_switch_violation(tree_model.T.nodes())
            if _i == number_of_requests - 1:
                self.update_clique_residual_and_next_clique_violation(bw, tree_model.links, 0)
                self.update_switch_entries_residual_and_next_switch_violation(tree_model.T.nodes())
            _i += 1

        if flag_success:
            print('consume resources: ', str(resource_consume))
        else:
            print('consume resources:   failure')
        return flag_success, resource_consume

    def update_reverse_link_cost(self):
        for clique_id, residual in self.copy_dict_clique_id_residual_capacity.items():
            _residual = 0.01 + residual
            for _link_id in self.tree_model_base.dict_clique_id_clique[clique_id]:
                _basic_link_cost = self.dict_link_id_link_cost_base[_link_id]
                self.dict_link_id_link_cost[_link_id] = _basic_link_cost / _residual

    def update_dynamic_link_cost(self, links_of_tree_models, nodes_of_tree_models):
        K_max_links = set([_link_id for clique_id in self.K_max_cliques
                           for _link_id in self.graph_model.dict_clique_id_clique[clique_id]])
        K_min_links = set([_link_id for clique_id in self.K_min_cliques
                           for _link_id in self.graph_model.dict_clique_id_clique[clique_id]])
        K_sw_max_links = set()
        K_sw_min_links = set()

        K_sw_else_max_links = set()
        K_sw_else_min_links = set()

        # it is always the scheme 0 who triumphs, by large.
        if self.sph_cost_scheme == 0:
            for clique_id in self.K_max_cliques:
                if any(_link_id in links_of_tree_models for _link_id
                       in self.graph_model.dict_clique_id_clique[clique_id]):
                    self.increase_cost_clique(clique_id, self.power)
                else:
                    self.increase_cost_clique(clique_id, self.power_else)
            for clique_id in self.K_min_cliques:
                if not any(_link_id in links_of_tree_models for _link_id
                           in self.graph_model.dict_clique_id_clique[clique_id]):
                    self.decrease_cost_clique(clique_id, K_sw_max_links, self.power)
                else:
                    self.decrease_cost_clique(clique_id, K_sw_max_links, self.power_else)

        elif self.sph_cost_scheme == 1:
            for clique_id in self.K_max_cliques:
                self.increase_cost_clique(clique_id, self.power)
            for clique_id in self.K_min_cliques:
                self.decrease_cost_clique(clique_id, K_sw_max_links, self.power)

        for node in self.K_sw_max_switches:
            # ----------- VERY IMPORTANT ---------- #
            if node in nodes_of_tree_models:
                for n in self.tree_model_base.G[node].keys():
                    _key = tuple(sorted((node, n)))
                    K_sw_max_links = K_sw_max_links.union(
                        self.graph_model.multi_link_info_dict[_key].links_set)

        for node in self.K_sw_max_switches:
            if node not in nodes_of_tree_models:
                for n in self.tree_model_base.G[node].keys():
                    _key = tuple(sorted((node, n)))
                    for link_id in self.graph_model.multi_link_info_dict[_key].links_set:
                        if link_id not in K_sw_max_links:
                            K_sw_else_max_links.add(link_id)

        for _link_id in K_sw_max_links:
            self.increase_cost_sw(_link_id, self.power_sw)

        for _link_id in K_sw_else_max_links:
            self.increase_cost_sw(_link_id, self.power_sw_else)

        for node in self.K_sw_min_switches:
            if node not in nodes_of_tree_models:
                for n in self.tree_model_base.G[node].keys():
                    _key = tuple(sorted((node, n)))
                    K_sw_min_links = K_sw_min_links.union(
                        self.graph_model.multi_link_info_dict[_key].links_set)

        for node in self.K_sw_min_switches:
            if node in nodes_of_tree_models:
                for n in self.tree_model_base.G[node].keys():
                    _key = tuple(sorted((node, n)))
                    for link_id in self.graph_model.multi_link_info_dict[_key].links_set:
                        if link_id not in K_sw_min_links:
                            K_sw_else_min_links.add(link_id)

        for _link_id in K_sw_min_links:
            self.decrease_cost_sw(_link_id, K_max_links, self.power_sw)

        for _link_id in K_sw_else_min_links:
            self.decrease_cost_sw(_link_id, K_max_links, self.power_sw_else)

        '''
        Enforce normal_cost only for _link_ids that
        belong to neither K_max(min)_cliques nor K_max(min)_switches.
        Option: do nothing with enforce_normal_cost.
        '''
        normal_links = set(range(1, self.graph_model.number_links_transmission + 1)) - \
                       K_max_links.union(K_min_links).union(K_sw_max_links).union(K_sw_min_links)
        for _link_id in normal_links:
            self.enforce_normal_cost(_link_id)

    def increase_cost_clique(self, clique_id, power):
        for _link_id in self.tree_model_base.dict_clique_id_clique[clique_id]:
            self.dict_link_id_link_cost[_link_id] *= float(power)

    #@idea: a link_id that is among the most saturated switches, should not get the minimizing bonus.
    def decrease_cost_clique(self, clique_id, K_sw_max_links, power):
        for _link_id in self.tree_model_base.dict_clique_id_clique[clique_id]:
            if _link_id not in K_sw_max_links:
                self.dict_link_id_link_cost[_link_id] *= float(1) / float(power)

    def increase_cost_sw(self, _link_id, power_sw):
        self.dict_link_id_link_cost[_link_id] *= float(power_sw)

    #@idea: a link_id that is among the most saturated cliques, should not get the minimizing bonus.
    def decrease_cost_sw(self, _link_id, K_max_links, power_sw):
        if _link_id in K_max_links:
            return
        self.dict_link_id_link_cost[_link_id] *= float(1) / float(power_sw)

    def enforce_normal_cost(self, _link_id):
        '''
        Or, do nothing with enforce_normal_cost.
        Result:  it is always the do_nothing == 0 who triumphs, by large.
        '''
        if self.do_nothing == 1:
            return
        self.dict_link_id_link_cost[_link_id] = self.dict_link_id_link_cost_base[_link_id]

