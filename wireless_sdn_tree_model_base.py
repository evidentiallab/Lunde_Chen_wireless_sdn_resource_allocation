from __future__ import print_function
import networkx as nx
import copy


class TreeModelBase(object):
    def __init__(self, graph_model):
        self.graph_model = graph_model
        self.G = copy.deepcopy(self.graph_model.G_int)
        self.number_nodes = self.graph_model.number_nodes
        self.number_links_transmission = self.graph_model.number_links_transmission
        self.list_nodes = self.G.nodes()
        self.multi_link_info_dict = self.graph_model.multi_link_info_dict
        self.multi_link_keys_set = self.graph_model.multi_link_keys_set
        self.multi_link_link_id_set = self.graph_model.multi_link_link_id_set
        self.int_link_transmission_dict = self.graph_model.int_link_transmission_dict
        self.transmission_int_link_key_dict = self.graph_model.transmission_int_link_key_dict
        self.dict_interference_pair_info = self.graph_model.dict_interference_pair_info
        self.dict_link_clique_id = self.graph_model.dict_link_clique_id
        self.dict_clique_id_residual_capacity = self.graph_model.dict_clique_id_residual_capacity
        self.dict_clique_id_clique = self.graph_model.dict_clique_id_clique
        self.bw_info_dict = self.graph_model.bw_info_dict
        self.of_table_info_dict = self.graph_model.of_table_info_dict
        self.local_multi_link_info_dict = {}

        self.req = None
        self.T = nx.Graph()

        self.all_links = set()

        self.links  = set()
        self.vlinks = set()

        self.dict_link_id_link_cost = None
        '''
        This dict should be have all multi-link keys.
        self.local_multi_link_info_dict = {(src, dst): (link_id, ch)}
        '''
        self.request_id = -1
        self.src        = -1
        self.list_dst   = []
        self.chapb = 0.9
        self.use_multicast_advantage = True
        self.one_by_one_overload_avoidance_strategy = 1
        self.cliques_not_satisfying_next = []
        self.multiplier_factor = 1.5

        self.obj_fun_parameters = None

    def determine_links_vlinks(self):
        self.links = set()
        self.vlinks = set()
        stack = [self.src]
        visited = set()
        while len(stack):
            node = stack.pop()
            visited.add(node)
            dict_ch_links = {}
            for n in self.T[node]:
                if n not in visited:
                    stack.append(n)
                    _key = tuple(sorted([node, n]))
                    if _key in self.multi_link_keys_set:
                        (_link_id, _ch) = self.local_multi_link_info_dict[_key]
                    else:
                        _link_id = list(self.multi_link_info_dict[_key].links_set)[0]
                        _ch = list(self.multi_link_info_dict[_key].channels_set)[0]
                    dict_ch_links.setdefault(_ch, []).append(_link_id)
            for _ch, _list_links in dict_ch_links.items():
                self.links.add(sorted(_list_links)[0])
                if len(_list_links) >= 2:
                    self.vlinks = self.vlinks.union(sorted(_list_links)[1:])

        '''
        Check that edges in T == links + vlinks
        If it's OK, this section of codes should be commented / removed.
        '''
        # edges_T = sorted([tuple(sorted(list(e))) for e in self.T.edges()])
        # links_all = sorted(self.transmission_int_link_key_dict[i] for i in list(self.links) + list(self.vlinks))
        # if len(edges_T) != len(links_all):
        #     print("ERROR: len(edges_T) != len(links_all)")
        #     return
        # for i in range(len(edges_T)):
        #     if edges_T[i] != links_all[i]:
        #         print("ERROR: edges_T[i] != links_all[i]")
        #         return

        if not self.use_multicast_advantage:
            self.links = self.links.union(self.vlinks)
            self.vlinks.clear()

    def init_link_costs(self):
        self.dict_link_id_link_cost = {}
        for i in range(1, self.number_links_transmission + 1):
            n_I = self.dict_interference_pair_info[i].num_of_interference_pairs
            link_cost = float(self.obj_fun_parameters[0] + self.obj_fun_parameters[1] + self.obj_fun_parameters[3] * n_I)
            self.dict_link_id_link_cost[i] = link_cost



