# coding: utf-8
from __future__ import print_function
import networkx as nx
from wireless_sdn_tree_model_base import TreeModelBase
import wireless_sdn_utils as utils
import copy
import random
import itertools
from heapq import heappop, heappush

class TreeModelGA(TreeModelBase):
    def __init__(self, graph_model):
        TreeModelBase.__init__(self, graph_model)

    def remove_non_src_non_dst_tree_branches_with_sph(self):
        z = [self.src] + self.list_dst

        steiner_edges = utils.sph_steiner_dijkstra(self.T, z)[0]
        remove_nodes_set = set()
        for e in self.T.edges():
            if (e[0], e[1]) not in steiner_edges and (e[1], e[0]) not in steiner_edges:
                self.T.remove_edge(*e)
                remove_nodes_set.add(e[0])
                remove_nodes_set.add(e[1])
        for node in remove_nodes_set:
            if len(self.T[node]) >= 1:
                continue
            self.T.remove_node(node)

    def connect_several_disconnected_components(self, weight='weight'):
        G = copy.deepcopy(self.G)
        for clique_id in self.cliques_not_satisfying_next:
            clique = self.dict_clique_id_clique[clique_id]
            '''
            Two things:
            --> 1. For a link * e * to have a punitive cost, * e * should be already in the channel to be penalized.
            --> 2. Should the mutation of channel should give a new link cost, 
                   taking into consideration clique violations? (Answer: no).
            '''
            for _link in clique:
                e = self.transmission_int_link_key_dict[_link]
                if self.local_multi_link_info_dict[e][0] == _link:
                    G[e[0]][e[1]][weight] = G[e[0]][e[1]][weight] * 50
        while 1:
            if nx.number_connected_components(self.T) == 1:
                break
            '''
            1. To sample out [T1, T2], perhaps a more randomized method could be used here ... (already done).
            2. The result seems to show that introducing more randomness degrades the quality of the solution ...
            3. This above observation is verified again in other experiments.
            '''
            [T1, T2] = list(nx.connected_component_subgraphs(self.T))[:2]
            # [T1, T2] = random.sample(list(nx.connected_component_subgraphs(self.T)), 2)
            glue_links = self.get_glue_links_between_two_sub_trees_with_multiplier_factor(
                copy.deepcopy(G), T1, T2, weight=weight)
            for e in glue_links:
                self.T.add_edge(*e, weight=self.G[e[0]][e[1]]["weight"])
        self.remove_non_src_non_dst_tree_branches_with_sph()
        self.determine_links_vlinks()

    def mutate_one_link(self):
        '''
        TODO? Mutation of links should give much more importance to the
        multi-link case. Perhaps not necessary.
        '''
        delete_edge_int = random.choice(list(self.links.union(self.vlinks)))
        _key = self.transmission_int_link_key_dict[delete_edge_int]
        if delete_edge_int in self.multi_link_link_id_set:
            if random.random() < self.chapb:
                multi_link_info = self.multi_link_info_dict[_key]
                while 1:
                    _link_id = random.choice(list(multi_link_info.links_set))
                    if _link_id != delete_edge_int:
                        break
                _ch = multi_link_info.link_channel_dict[_link_id]
                self.G[_key[0]][_key[1]]["weight"] = self.dict_link_id_link_cost[_link_id]

                '''
                We should comment out those codes, as mutation happen when all crossover is finished, and hence 
                self.cliques_not_satisfying_next has no sense for the mutation !
                '''
                # for clique_id in self.cliques_not_satisfying_next:
                #     clique = self.dict_clique_id_clique[clique_id]
                #     if _link_id in clique:
                #         self.G[_key[0]][_key[1]]["weight"] = self.G[_key[0]][_key[1]]["weight"] * 50

                self.local_multi_link_info_dict[_key] = (_link_id, _ch)
                # TODO: Re-determine links and vlinks. This could be optimized later.
                self.determine_links_vlinks()
                return
        self.T.remove_edge(*_key)
        if nx.number_connected_components(self.T) != 2:
            print("Error, nx.number_connected_components(T) != 2")
            return
        [T1, T2] = list(nx.connected_component_subgraphs(self.T))
        glue_links = self.get_glue_links_between_two_sub_trees_with_multiplier_factor(copy.deepcopy(self.G), T1, T2)
        for e in glue_links:
            self.T.add_edge(*e, weight=self.G[e[0]][e[1]]["weight"])
        if nx.number_connected_components(self.T) != 1:
            print("nx.number_connected_components(self.T) != 1")
            return
        '''
        Branches of the tree that do not contain source or destination nodes should be removed.
        '''
        self.remove_non_src_non_dst_tree_branches_with_sph()
        self.determine_links_vlinks()

    def get_glue_links_between_two_sub_trees_with_one_random_k_shortest_path(self, G, T1, T2, weight='weight'):
        nodes_src = T1.nodes()
        nodes_dst = T2.nodes()
        edges_src = T1.edges()
        edges_dst = T2.edges()
        source = "src"
        target = "dst"
        G.add_node(source)
        G.add_node(target)
        for e in edges_src:
            G.remove_edge(*e)
        for e in edges_dst:
            G.remove_edge(*e)
        for node in nodes_src:
            G.add_edge(node, source, weight=0)
        for node in nodes_dst:
            G.add_edge(node, target, weight=0)
        for e in G.edges():
            G[e[0]][e[1]][weight] = int(G[e[0]][e[1]][weight] * (1 + random.random() * (self.multiplier_factor - 1)))
        cost, path = nx.single_source_dijkstra(G, source, target, weight=weight)
        if target not in cost:
            raise nx.NetworkXNoPath("node %s not reachable from %s" % (source, target))

        def get_path_cost(G, _path, weight='weight'):
            _cost = 0
            if len(_path) > 1:
                for i in range(len(_path) - 1):
                    u = _path[i]
                    v = _path[i + 1]
                    _cost += G.edge[u][v].get(weight, 1)
            return _cost

        costs = [cost[target]]
        paths = [path[target]]
        c = itertools.count()
        B = []
        G_original = G.copy()

        '''
        k is a random int in [1, 2, 3, 4, 5]
        '''
        k = random.randint(1, 5)

        for i in range(1, k):
            for j in range(len(paths[-1]) - 1):
                spur_node = paths[-1][j]
                root_path = paths[-1][:j + 1]

                edges_removed = []
                for c_path in paths:
                    if len(c_path) > j and root_path == c_path[:j + 1]:
                        u = c_path[j]
                        v = c_path[j + 1]
                        if G.has_edge(u, v):
                            edge_attr = G.edge[u][v]
                            G.remove_edge(u, v)
                            edges_removed.append((u, v, edge_attr))

                for n in range(len(root_path) - 1):
                    node = root_path[n]
                    # out-edges
                    for u, v, edge_attr in G.edges_iter(node, data=True):
                        G.remove_edge(u, v)
                        edges_removed.append((u, v, edge_attr))

                    if G.is_directed():
                        # in-edges
                        for u, v, edge_attr in G.in_edges_iter(node, data=True):
                            G.remove_edge(u, v)
                            edges_removed.append((u, v, edge_attr))

                spur_path_cost, spur_path = nx.single_source_dijkstra(G, spur_node, target, weight=weight)
                if target in spur_path and spur_path[target]:
                    total_path = root_path[:-1] + spur_path[target]
                    total_path_cost = get_path_cost(G_original, root_path, weight) + spur_path_cost[target]
                    heappush(B, (total_path_cost, next(c), total_path))

                for e in edges_removed:
                    u, v, edge_attr = e
                    G.add_edge(u, v, edge_attr)

            if B:
                (l, _, p) = heappop(B)
                costs.append(l)
                paths.append(p)
            else:
                break

        route = [paths[target]][0]
        glue_links = []
        for i in range(1, len(route) - 2):
            glue_links.append(tuple(sorted(list((route[i], route[i + 1])))))
        return glue_links

    def get_glue_links_between_two_sub_trees_with_multiplier_factor(self, G, T1, T2, weight='weight'):
        '''
        Instead of using k-shortest-path and draw one from them (to bring mutations),
        we vary stochastically the weight associated to non-tree links, and calculate the
        shortest path between two trees, as presented in our Steiner tree paper.
        '''
        nodes_src = T1.nodes()
        nodes_dst = T2.nodes()
        edges_src = T1.edges()
        edges_dst = T2.edges()
        source = "src"
        target = "dst"
        G.add_node(source)
        G.add_node(target)
        for e in edges_src:
            G.remove_edge(*e)
        for e in edges_dst:
            G.remove_edge(*e)
        for node in nodes_src:
            G.add_edge(node, source, weight=0)
        for node in nodes_dst:
            G.add_edge(node, target, weight=0)
        for e in G.edges():
            G[e[0]][e[1]][weight] = G[e[0]][e[1]][weight] * (1 + random.random() * (self.multiplier_factor - 1))
        if source == target:
            return ([0], [[source]])
        cost, path = nx.single_source_dijkstra(G, source, target, weight=weight)
        if target not in cost:
            raise nx.NetworkXNoPath("node %s not reachable from %s" % (source, target))
        route = [path[target]][0]
        glue_links = []
        for i in range(1, len(route) - 2):
            glue_links.append(tuple(sorted(list((route[i], route[i + 1])))))
        return glue_links

    def get_glue_links_between_two_sub_trees_with_multiplier_factor_csgraph(self, _G, T1, T2, weight='weight'):
        '''
        Not finished yet. Not a feasible solution.
        '''
        from scipy.sparse.csgraph import dijkstra
        S = self.S.copy()
        nodes_src = T1.nodes()
        nodes_dst = T2.nodes()
        edges_src = T1.edges()
        edges_dst = T2.edges()
        source = 0
        target = self.number_nodes + 1

        for e in edges_src:
            S[(e[0], e[1])] = 0
            S[(e[1], e[0])] = 0
        for e in edges_dst:
            S[(e[0], e[1])] = 0
            S[(e[1], e[0])] = 0
        for node in nodes_src:
            S[(source, node)] = 0.1
            S[(node, source)] = 0.1
        for node in nodes_dst:
            S[(target, node)] = 0.1
            S[(node, target)] = 0.1
        # for e in G.edges():
        #     G[e[0]][e[1]][weight] = G[e[0]][e[1]][weight] * (1 + random.random() * 0.2)
        dist_matrix, predecessors = dijkstra(S, directed=False, indices=[0, self.number_nodes + 1], return_predecessors=True)
        node = target
        glue_links = []
        while node != source:
            pre = predecessors[source, node]
            glue_links.append((pre, node))
            node = pre
        return glue_links[1:][:-1]

    def get_glue_links_between_two_sub_trees_with_multiplier_factor_gt(self, _G, T1, T2, weight='weight'):
        import graph_tool as gt  # Note: copy graph_tool source code to Python27/Lib/site-packages
        from graph_tool.all import shortest_path
        edges_to_remove = T1.edges() + T2.edges()
        nodes_src = T1.nodes()
        nodes_dst = T2.nodes()

        dict_i_vertex_index = {}
        dict_e_edge = {}
        dict_edge_e = {}
        G = gt.Graph(directed=False)
        dict_prop_double = G.new_edge_property("double")

        for node in self.G.nodes():
            # if node in nodes_src or node in nodes_dst:
            dict_i_vertex_index[node] = G.vertex_index[G.add_vertex()]
        source = -1
        target = -2
        dict_i_vertex_index[source] = G.vertex_index[G.add_vertex()]  # node -1 corresponds to the source node
        dict_i_vertex_index[target] = G.vertex_index[G.add_vertex()]  # node -2 corresponds to the target node

        for e in self.G.edges():
            if (e[0], e[1]) not in edges_to_remove and (e[1], e[0]) not in edges_to_remove:
                edge = G.add_edge(G.vertex(dict_i_vertex_index[e[0]]), G.vertex(dict_i_vertex_index[e[1]]))
                dict_e_edge[tuple(sorted(list(e)))] = edge
                dict_edge_e[edge] = tuple(sorted(list(e)))
                dict_prop_double[edge] = self.G[e[0]][e[1]]["weight"] * (1 + random.random() * (self.multiplier_factor - 1))

        for node in nodes_src:
            edge = G.add_edge(G.vertex(dict_i_vertex_index[node]), G.vertex(dict_i_vertex_index[source]))
            dict_e_edge[(source, node)] = edge
            dict_edge_e[edge] = (source, node)
            dict_prop_double[edge] = 0.0
        for node in nodes_dst:
            edge = G.add_edge(G.vertex(dict_i_vertex_index[node]), G.vertex(dict_i_vertex_index[target]))
            dict_e_edge[(target, node)] = edge
            dict_edge_e[edge] = (target, node)
            dict_prop_double[edge] = 0.0

        res_vertex_list, res_edge_list = shortest_path(
            G, G.vertex(dict_i_vertex_index[source]), G.vertex(dict_i_vertex_index[target]), weights=dict_prop_double)

        res_vertex_index_list = map(lambda x: G.vertex_index[x], res_vertex_list)
        if dict_i_vertex_index[target] not in res_vertex_index_list:
            raise nx.NetworkXNoPath("node %s not reachable from %s" % (source, target))
        res_edge_list = res_edge_list[1:][:-1]
        glue_links = map(lambda x: dict_edge_e[x], res_edge_list)

        return glue_links

    def create_random_sph_steiner_tree_from_static_link_cost(self):
        G = copy.deepcopy(self.G)
        for e in G.edges():
            G[e[0]][e[1]]["weight"] = self.G[e[0]][e[1]]["weight"] * (1 + random.random() * (self.multiplier_factor - 1))
        z = [self.src] + self.list_dst
        steiner_edges = utils.sph_steiner_dijkstra(G, z)[0]
        for e in steiner_edges:
            self.T.add_edge(*e, weight=self.G[e[0]][e[1]]["weight"])

    def create_random_sph_steiner_tree_from_dynamic_link_cost(self):
        copy_dict_link_id_link_cost = copy.deepcopy(self.dict_link_id_link_cost)
        for _link_id, _cost in copy_dict_link_id_link_cost.items():
            copy_dict_link_id_link_cost[_link_id] = _cost * (1 + random.random() * (self.multiplier_factor - 1))
        for _key in self.G.edges():
            multi_link_info = self.multi_link_info_dict[_key]
            _link_id = min(list(multi_link_info.links_set), key=lambda link: copy_dict_link_id_link_cost[link])
            _ch = multi_link_info.link_channel_dict[_link_id]
            self.local_multi_link_info_dict[_key] = (_link_id, _ch)
            self.G[_key[0]][_key[1]]["weight"] = copy_dict_link_id_link_cost[_link_id]
        z = [self.src] + self.list_dst
        steiner_edges = utils.sph_steiner_dijkstra(self.G, z)[0]
        for e in steiner_edges:
            self.T.add_edge(*e, weight=self.G[e[0]][e[1]]["weight"])


def compare_computation_time_our_sph_vs_nx_single_source_dijkstra(weight='weight'):
    import wireless_sdn_replay_helper as replay
    import time
    gm = replay.load_graph_model("wireless_sdn_pickles/network_model_" + str(1) + "/1")
    G = gm.G_int
    for e in G.edges():
        G[e[0]][e[1]]["weight"] = random.uniform(1, 100)
        # G[e[0]][e[1]]["weight"] = random.randint(1, 100)

    elapsed_time_nx, elapsed_time_sph = 0, 0

    for i in range(1000000):
        [src, dst] = random.sample(range(1, gm.number_nodes + 1), 2)
        start_time_nx = time.time()
        dict_cost_nx, _dict_path_nx = nx.single_source_dijkstra(G, src, dst, weight=weight)
        elapsed_time_nx += time.time() - start_time_nx
        cost_nx = dict_cost_nx[dst]
        start_time_sph = time.time()
        (_edges, cost_sph) = utils.sph_steiner_dijkstra(G, [src, dst], metric=weight)
        elapsed_time_sph += time.time() - start_time_sph
        if int(cost_nx) != int(cost_sph):
            print("ERROR, cost_nx != cost_sph", cost_nx, ' ', cost_sph)
            break
        if i % 10000 == 0:
            print(i, '\n')
    print('elapsed_time_nx  : ', elapsed_time_nx)
    print('elapsed_time_sph : ', elapsed_time_sph)
    print("compare_computation_time_our_sph_vs_nx_single_source_dijkstra finished.")

    '''
    Experiment 1 results:
    elapsed_time_nx  :  59.8909945488
    elapsed_time_sph :  166.145017147
    
    Experiment 2 results:
    elapsed_time_nx  :  61.0500135422
    elapsed_time_sph :  167.210984468
    '''


if __name__ == '__main__':
    compare_computation_time_our_sph_vs_nx_single_source_dijkstra()
