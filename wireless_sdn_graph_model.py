from __future__ import print_function
import networkx as nx
from random import randint
import math
import random
import wireless_sdn_utils
from wireless_sdn_network_info import *
import time
from datetime import datetime
import dill


class ResourceModel(object):
    def __init__(self, number_nodes, number_links_transmission):
        self.total_bw_consumed = 0
        self.total_interference_brought = 0

        self.dict_link_id_total_bw_consumption = {i: 0 for i in range(1, number_links_transmission + 1)}
        self.dict_node_id_openflow_table_decrease = {i: 0 for i in range(1, number_nodes + 1)}
        self.dict_node_id_group_table_decrease = {i: 0 for i in range(1, number_nodes + 1)}

    def __str__(self):
        return str(
            " total_bw_consumed: "
            + str(self.total_bw_consumed)
            + " , total_interference_brought: "
            + str(self.total_interference_brought)
            + " , dict_node_id_openflow_table_decrease: "
            + str(self.dict_node_id_openflow_table_decrease)
            + " , dict_node_id_group_table_decrease:"
            + str(self.dict_node_id_group_table_decrease))


class GraphModel(object):
    def __init__(self, number_nodes=20,
                 number_links_transmission=60,
                 number_extra_conflict_link_pairs=20,
                 number_of_cliques_min=10,  # if number_of_cliques_min <= 0: no limit
                 number_of_cliques_max=17,
                 number_of_channels=7,
                 min_number_link_of_each_channel=6,
                 max_number_link_of_each_channel=10,
                 transmission_range=6,
                 interference_range=9,
                 transmission_connection_ratio=0.9,
                 clique_based=True,
                 json_channels={1: {"color": "violet", "capacity": 1024},
                                2: {"color": "blue", "capacity": 1024},
                                3: {"color": "orange", "capacity": 1024},
                                4: {"color": "green", "capacity": 1024},
                                5: {"color": "yellow", "capacity": 1024},
                                6: {"color": "red", "capacity": 1024},
                                7: {"color": "gray", "capacity": 1024},
                                },
                 number_of_openflow_entries=2000, number_of_group_entries=50, xylimit=18, file_type=".png"):

        self.xlimit = xylimit
        self.ylimit = xylimit
        self.file_type = file_type
        self.number_nodes = number_nodes
        self.number_of_cliques_min = number_of_cliques_min
        self.number_of_cliques_max = number_of_cliques_max
        self.transmission_connection_ratio = transmission_connection_ratio
        self.transmission_range = transmission_range
        self.interference_range = interference_range
        self.number_of_openflow_entries = number_of_openflow_entries
        self.number_of_group_entries = number_of_group_entries
        self.json_channels = json_channels
        self.list_channels = range(1, number_of_channels + 1)
        self.set_channels_used = set()
        self.number_channels = number_of_channels
        self.channel_info_dict = {ch: ChannelInfo(ch) for ch in self.list_channels}
        self.shared_trans_link_channel_info_dict = {ch: SharedTransLinkChannelInfo(ch) for ch in self.list_channels}
        self.bw_info_dict = {}
        self.of_table_info_dict = {}
        self.multi_link_info_dict = {}
        self.multi_link_keys_set  = set()
        self.multi_link_link_id_set  = set()
        self.transmission_int_link_key_dict  = {}
        self.str_time = time.strftime("%Y%m%d%H%M%S") + str(int(int(datetime.utcnow().strftime('%f')) / 1000))
        self.G = nx.Graph()
        self.G_int = nx.Graph()
        self.node_int_xy_dict = {}
        self.node_xy_int_dict = {}
        self.node_int_node_instance_dict = {}
        self.is_connected = True
        self.is_constructed = False
        self.node_labels = {}
        self.clique_based = clique_based

        self.number_links_transmission = number_links_transmission
        self.number_extra_conflict_link_pairs = number_extra_conflict_link_pairs

        self.dict_channel_conflict_links = {ch: [] for ch in self.list_channels}
        self.dict_channel_cliques = {ch: [] for ch in self.list_channels}
        self.all_cliques = []
        self.clique_id = 1
        '''
        ATTENTION: clique_id is ranged from 2 to self.graph_model_ilp.clique_id
        '''
        self.dict_link_clique_id = {lid: set() for lid in range(1, self.number_links_transmission + 1)}
        self.dict_clique_id_residual_capacity = {}
        self.dict_clique_id_clique = {}

        '''
        Set up nodes. Each pair of nodes, their distance should be greater than 3.3.
        '''
        count = 1
        list_nodes = []
        while True:
            x = random.random() * self.xlimit
            y = random.random() * self.ylimit
            xy = (x, y)
            flag = False
            for n in list_nodes:
                if self.dist_node_xy(n, xy) <= 1.6:
                    flag = True
                    break
            if flag:
                continue
            self.G.add_node(xy)
            self.G_int.add_node(count)
            self.node_int_xy_dict[count] = xy
            self.node_xy_int_dict[xy] = count
            node = Node()
            node.index = count
            node.xy = xy
            node.openflow_entries_residu = self.number_of_openflow_entries
            node.group_entries_residu    = self.number_of_group_entries
            self.node_int_node_instance_dict[count] = node
            self.node_labels[xy] = count
            list_nodes.append(xy)

            of_table_info = OpenFlowTablesInfo(count)
            of_table_info.get_attributes_from_node(node)
            self.of_table_info_dict[count] = of_table_info

            count += 1
            if count > self.number_nodes:
                break

        node_channel_dict_tmp = {}
        for i, xy in self.node_int_xy_dict.items():
            # channels = sorted(random.sample(self.list_channels, randint(1, self.number_channels)))
            '''
            We limit the number of channels each node could have to 3.
            '''
            channels = sorted(random.sample(self.list_channels, randint(1, min(3, self.number_channels))))
            node_channel_dict_tmp[i] = channels

        self.int_link_illustration_dict = {}
        self.int_link_transmission_dict = {}

        dict_ch_list_trans_links = {ch: [] for ch in self.list_channels}

        count = 0
        for i in range(1, self.number_nodes + 1):
            for j in range(i + 1, self.number_nodes + 1):
                if self.is_within_transmission_range(i, j):
                    for ch in self.list_channels:
                        if ch in node_channel_dict_tmp[i] and ch in node_channel_dict_tmp[j]:
                            if random.random() <= self.transmission_connection_ratio:
                                self.set_channels_used.add(ch)
                                dict_ch_list_trans_links[ch].append((i, j))
                                count += 1
        if count < self.number_links_transmission:
            return
        if len(self.set_channels_used) != self.number_channels:
            return

        for ch in self.list_channels:
            if len(dict_ch_list_trans_links[ch]) < min_number_link_of_each_channel:
                return
        _next = True
        while count > self.number_links_transmission:
            if _next:
                ch = random.choice(self.list_channels)
            _len = len(dict_ch_list_trans_links[ch])
            if _len > min_number_link_of_each_channel:
                count -= 1
                del dict_ch_list_trans_links[ch][randint(0, _len - 1)]
                _len -= 1
            if _len > max_number_link_of_each_channel:
                _next = False
            else:
                _next = True

        count = 0
        for ch in self.list_channels:
            list_trans_links = dict_ch_list_trans_links[ch]
            for int_int_pair in list_trans_links:
                (i, j) = int_int_pair
                count += 1
                link = Link()
                link.index = count
                link.channel = ch
                link.src = i
                link.dst = j
                link.color     = self.json_channels.get(ch).get("color")
                link.capacity  = self.json_channels.get(ch).get("capacity")
                link.bw_residu = self.json_channels.get(ch).get("capacity")

                link_transmission = LinkTransmission()
                link_transmission.get_attributes_from_link(link)
                link_illustration = LinkIllustration()
                link_illustration.get_attributes_from_link(link_transmission)

                bw_info = BandwidthInfo(count)
                bw_info.get_attributes_from_link(link)
                self.bw_info_dict[count] = bw_info

                self.int_link_illustration_dict[count] = link_illustration
                self.int_link_transmission_dict[count] = link_transmission
                self.node_int_node_instance_dict[i].links_illustration.setdefault(j, []).append(
                    link_illustration)
                self.node_int_node_instance_dict[i].links_transmission.setdefault(j, []).append(
                    link_transmission)

                self.transmission_int_link_key_dict[count] = (i, j)

                self.node_int_node_instance_dict[i].channels.add(ch)
                self.G.add_edge(self.node_int_xy_dict[i], self.node_int_xy_dict[j])
                self.G_int.add_edge(i, j)
                self.channel_info_dict[ch].nodes_set.add(i)
                self.channel_info_dict[ch].nodes_set.add(j)
                self.channel_info_dict[ch].links_set.add(link_transmission)
                self.channel_info_dict[ch].links_list.append(count)
                self.channel_info_dict[ch].tuples_set.add((i, j))

                '''
                Multi-link information is pre-processed here.
                '''
                multi_link_info = self.multi_link_info_dict.setdefault((i, j), MultiLinkInfo(i, j))
                multi_link_info.channels_set.add(ch)
                multi_link_info.links_set.add(count)
                multi_link_info.channel_link_dict[ch] = count
                multi_link_info.link_channel_dict[count] = ch
                self.multi_link_info_dict[(i, j)] = multi_link_info

                if i not in self.shared_trans_link_channel_info_dict[ch].set_src:
                    self.shared_trans_link_channel_info_dict[ch].set_src.add(i)
                    self.shared_trans_link_channel_info_dict[ch].dict_src_link_tuple[i] = (i, j)
                    self.shared_trans_link_channel_info_dict[ch].dict_link_tuple_link_tuple[(i, j)] = (i, j)
                    self.shared_trans_link_channel_info_dict[ch].list_shared_link_tuples.append((i, j))
                    self.shared_trans_link_channel_info_dict[ch].number_of_shared_links += 1
                else:
                    self.shared_trans_link_channel_info_dict[ch].dict_link_tuple_link_tuple[(i, j)] = \
                        self.shared_trans_link_channel_info_dict[ch].dict_src_link_tuple[i]

                if j not in self.shared_trans_link_channel_info_dict[ch].set_src:
                    self.shared_trans_link_channel_info_dict[ch].set_src.add(j)
                    self.shared_trans_link_channel_info_dict[ch].dict_src_link_tuple[j] = (j, i)
                    self.shared_trans_link_channel_info_dict[ch].dict_link_tuple_link_tuple[(j, i)] = (j, i)
                    self.shared_trans_link_channel_info_dict[ch].list_shared_link_tuples.append((j, i))
                    self.shared_trans_link_channel_info_dict[ch].number_of_shared_links += 1
                else:
                    self.shared_trans_link_channel_info_dict[ch].dict_link_tuple_link_tuple[(j, i)] = \
                        self.shared_trans_link_channel_info_dict[ch].dict_src_link_tuple[j]

        if not nx.is_connected(self.G):
            self.is_connected = False
        if nx.number_connected_components(self.G) != 1:
            self.is_connected = False
        if not self.is_connected:
            return

        for _key, multi_link_info in self.multi_link_info_dict.items():
            if len(multi_link_info.links_set) >= 2:
                self.multi_link_keys_set.add(_key)
                self.multi_link_link_id_set = self.multi_link_link_id_set.union(multi_link_info.links_set)
                multi_link_info.is_multi_link = True

        for ch in self.list_channels:
            channel_info = self.channel_info_dict[ch]
            links = sorted(list(channel_info.links_set))
            size = len(links)
            for i in range(size - 1):
                if links[i].index > self.number_links_transmission:
                    continue
                for j in range(i + 1, size):
                    if links[j].index > self.number_links_transmission:
                        continue
                    a, b = links[i].src, links[i].dst
                    c, d = links[j].src, links[j].dst
                    if a == c or a == d or b == c or b == d:
                        self.dict_channel_conflict_links[ch].append(tuple(sorted(list((links[i].index, links[j].index)))))

        if self.number_extra_conflict_link_pairs >= 0:
            count = 0
            loop = 0
            while count < self.number_extra_conflict_link_pairs:
                loop += 1
                if loop >= 20 * self.number_extra_conflict_link_pairs:
                    break
                ch = random.choice(self.list_channels)
                channel_info = self.channel_info_dict[ch]
                links = sorted(list(channel_info.links_set))
                size = len(links)
                if size <= 1:
                    continue
                i = randint(0, size - 2)
                j = randint(i + 1, size - 1)
                if tuple(sorted(list((links[i].index, links[j].index)))) in self.dict_channel_conflict_links[ch]:
                    continue
                a, b = links[i].src, links[i].dst
                c, d = links[j].src, links[j].dst
                if a == c or a == d or b == c or b == d:
                    continue
                if any(tuple(sorted(one_hop_link)) in channel_info.tuples_set for one_hop_link in
                         [(a, c), (a, d), (b, c), (b, d)]):
                    count += 1
                    self.dict_channel_conflict_links[ch].append(tuple(sorted(list((links[i].index, links[j].index)))))
            loop = 0
            while count < self.number_extra_conflict_link_pairs:
                loop += 1
                if loop >= 20 * self.number_extra_conflict_link_pairs:
                    self.interference_range *= 2
                if loop >= 50 * self.number_extra_conflict_link_pairs:
                    break
                ch = random.choice(self.list_channels)
                _len = len(dict_ch_list_trans_links[ch])
                if _len <= 2:
                    continue
                la = random.choice(dict_ch_list_trans_links[ch])
                lb = random.choice(dict_ch_list_trans_links[ch])
                if la == lb:
                    continue
                if la[0] == lb[0] or la[0] == lb[1] or la[1] == lb[0] or la[1] == lb[1]:
                    continue
                if self.is_within_interference_range(la[0], lb[0]) or \
                        self.is_within_interference_range(la[0], lb[1]) or \
                        self.is_within_interference_range(la[1], lb[0]) or \
                        self.is_within_interference_range(la[1], lb[1]):
                    id_a = self.multi_link_info_dict[(la[0], la[1])].channel_link_dict[ch]
                    id_b = self.multi_link_info_dict[(lb[0], lb[1])].channel_link_dict[ch]
                    if id_a > id_b:
                        id_a, id_b = id_b, id_a
                    if (id_a, id_b) not in self.dict_channel_conflict_links[ch]:
                        self.dict_channel_conflict_links[ch].append((id_a, id_b))
                        count += 1

            if count < self.number_extra_conflict_link_pairs:
                return
        else:
            count = 0
            loop = 0
            while count > self.number_extra_conflict_link_pairs:
                ch = random.choice(self.list_channels)
                loop += 1
                if loop >= -1 * 500 * self.number_extra_conflict_link_pairs:
                    break
                if len(self.dict_channel_conflict_links[ch]):
                    _del = random.choice(range(len(self.dict_channel_conflict_links[ch])))
                    del self.dict_channel_conflict_links[ch][_del]
                    count -= 1

        self.number_links_transmission = len(self.int_link_transmission_dict)

        # Equivalent to dict(zip(self.G.nodes(), self.G.nodes()))
        # A better solution: dict(zip(self.G_int.nodes(), self.G.nodes()))
        self.pos = dict(zip(self.G, self.G))

        self.dict_interference_pair_info = {link_id: InterferencePairInfo(link_id)
                                            for link_id in range(1, self.number_links_transmission + 1)}
        n_cliques = 0
        for ch in self.list_channels:
            self.build_interference_pairs(ch)
            n_cliques += self.build_cliques(ch)
        print("n_cliques = ", n_cliques)
        if self.number_of_cliques_min > 0:
            if not self.number_of_cliques_min <= n_cliques <= self.number_of_cliques_max:
                return
        self.is_constructed = True

    def save(self):
        with open(self.str_time + "_gm_pickle", 'wb') as f:
            dill.dump(self, f)

    #see: https://stackoverflow.com/questions/2709800/how-to-pickle-yourself
    def load(self, obj):
        self.__dict__.update(dill.loads(obj).__dict__)

    def consume_resource(self, resource_model, flag_consume=True):
        neg = 1
        if not flag_consume:
            neg *= -1
        for link_id, capacity_decrease in resource_model.dict_link_id_total_capacity_decrease.items():
            self.bw_info_dict[link_id].bw_residu -= int(neg * capacity_decrease)
        for node_id, openflow_table_decrease in resource_model.dict_node_id_openflow_table_decrease.items():
            self.of_table_info_dict[node_id].openflow_entries_residu -= neg * openflow_table_decrease
        for node_id, group_table_decrease in resource_model.dict_node_id_group_table_decrease.items():
            self.of_table_info_dict[node_id].group_entries_residu -= neg * group_table_decrease

    def recover_resource(self, resource_model):
        self.consume_resource(resource_model, flag_consume=False)

    def build_interference_pairs(self, ch):
        for (i, j) in self.dict_channel_conflict_links[ch]:
            self.dict_interference_pair_info[i].set_interference_links.add(j)
            self.dict_interference_pair_info[j].set_interference_links.add(i)
            self.dict_interference_pair_info[i].num_of_interference_pairs += 1
            self.dict_interference_pair_info[j].num_of_interference_pairs += 1

    def build_cliques(self, ch, clique_size_at_least_three=True):
        # CG means conflict graph
        CG = nx.Graph()
        for (i, j) in self.dict_channel_conflict_links[ch]:
            CG.add_edge(i, j)
        if self.clique_based:
            _cliques = list(nx.find_cliques(CG))
        else:
            '''
            @Attention ! Cliques of size of 2 are not presented to cliques constraints (for plotting/illustration reasons), 
            but are taken into consideration in the objective function calculation, which
            could be problematic in some extreme corner cases.
            '''
            if clique_size_at_least_three:
                _cliques = filter(lambda x: len(x) >= 3, list(nx.connected_components(CG)))
            else:
                _cliques = list(nx.connected_components(CG))
        self.dict_channel_cliques[ch] += _cliques
        self.all_cliques += _cliques
        for _clique in _cliques:
            self.clique_id += 1
            self.dict_clique_id_residual_capacity[self.clique_id] = self.json_channels[ch].get("capacity")
            self.dict_clique_id_clique[self.clique_id] = _clique
            for link_id in _clique:
                self.dict_link_clique_id[link_id].add(self.clique_id)
        return len(_cliques)

    def build_ellipsoids(self, ch, ellipsoid_size_at_least_three=True):
        from matplotlib.patches import Ellipse
        import numpy as np

        CG = nx.Graph()
        list_ellipsoids = []
        color = self.json_channels.get(ch).get("color")

        for (i, j) in self.dict_channel_conflict_links[ch]:
            link_1 = self.int_link_transmission_dict[i]
            link_2 = self.int_link_transmission_dict[j]
            a, b = link_1.src, link_1.dst
            c, d = link_2.src, link_2.dst
            (x1, y1) = self.node_int_xy_dict[a]
            (x2, y2) = self.node_int_xy_dict[b]
            (x3, y3) = self.node_int_xy_dict[c]
            (x4, y4) = self.node_int_xy_dict[d]
            mid_1 = ((x1 + x2) / float(2), (y1 + y2) / float(2))
            mid_2 = ((x3 + x4) / float(2), (y3 + y4) / float(2))
            CG.add_edge(mid_1, mid_2)

        '''
        In coherence to @WhatToDo, here the code should also change.
        '''
        if self.clique_based:
            cliques = list(nx.find_cliques(CG))
        else:
            cliques = filter(lambda x: len(x) >= 3, list(nx.connected_components(CG)))

        for elli_points in cliques:
            '''
            @Attention: If ellipsoid_size_at_least_three is set to true, 
            only cliques with more than 2 nodes are drawn in the illustration file. 
            But in calculation, those 2-nodes cliques should also be included, 
            if they are not already included in a larger clique.
            Comment the two lines if you want to check its effect.
            '''
            if ellipsoid_size_at_least_three:
                if len(elli_points) <= 2:
                    continue
            numpy_P = np.zeros((len(elli_points), 2))
            index_p = 0
            for p in elli_points:
                numpy_P[index_p] = [p[0], p[1]]
                index_p += 1
            (center, radii, rotation) = wireless_sdn_utils.minimum_vol_ellipsoid(P=numpy_P)
            r1, r2 = radii[1] + 0.1, radii[0] + 0.1
            possible_angles = [math.atan2(rotation[0][1], rotation[0][0]),
                               - math.atan2(rotation[0][1], rotation[0][0]),
                               math.atan2(rotation[1][1], rotation[1][0]),
                               - math.atan2(rotation[0][1], rotation[0][0])]
            for _angle in possible_angles:
                angle = _angle
                number_p_in_ellipsoid = 0
                for p in elli_points:
                    (p_r_x, p_r_y) = self.rotate_point(center, p, -1 * angle)  # reverse rotate the point.
                    if (p_r_x - center[0]) ** 2 / r1 ** 2 + (p_r_y - center[1]) ** 2 / r2 ** 2 <= 1:
                        number_p_in_ellipsoid += 1
                if number_p_in_ellipsoid == len(elli_points):
                    break
            w, h = 2 * radii[1] + 0.5, 2 * radii[0] + 0.5
            angle360 = 180 * angle / math.pi
            elli = Ellipse(xy=center, width=w, height=h, angle=angle360, color=color, alpha=0.3)
            list_ellipsoids.append(elli)
        conflict_edges = []
        return CG, list_ellipsoids, conflict_edges

    def check_is_constructed(self):
        return self.is_constructed

    def illustrate(self):
        single_edges = []
        double_edges = []
        triple_edges = []
        for i in range(1, self.number_nodes + 1):
            node = self.node_int_node_instance_dict[i]
            for j, list_link_illustr in node.links_illustration.items():
                if len(list_link_illustr) == 1:
                    li = list_link_illustr[0]
                    single_edges.append((li.src, li.dst, li.color, li.line_style))
                elif len(list_link_illustr) == 2:
                    li1 = list_link_illustr[0]
                    li2 = list_link_illustr[1]
                    double_edges.append((li1.src, li1.dst, li1.color, li2.color, li1.line_style, li2.line_style))
                elif len(list_link_illustr) == 3:
                    li1 = list_link_illustr[0]
                    li2 = list_link_illustr[1]
                    li3 = list_link_illustr[2]
                    triple_edges.append((li1.src, li1.dst, li1.color, li2.color,
                                         li3.color, li1.line_style, li2.line_style, li3.line_style))

        self.draw_and_save_edges(single_edges, double_edges, triple_edges, self.str_time + self.file_type)
        all_ellipsoids = []
        for ch in self.set_channels_used:
            try:
                color = self.json_channels.get(ch).get("color")
                CG, list_ellipsoids, conflict_edges = self.build_ellipsoids(ch)
                for i in range(len(list_ellipsoids)):
                    file_name = self.str_time + "_cliques_ch_" + color + "elli_" + str(i) + self.file_type
                    # self.draw_and_save_edges(single_edges, double_edges, triple_edges, file_name, list_ellipsoids=[list_ellipsoids[i]])
                all_ellipsoids += list_ellipsoids
            except Exception:
                continue
        file_name = self.str_time + "_cliques_all" + self.file_type
        self.draw_and_save_edges(single_edges, double_edges, triple_edges, file_name, list_ellipsoids=all_ellipsoids)

    def dist_node_xy(self, node1, node2):
        (x1, y1) = node1
        (x2, y2) = node2
        return  math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def is_within_transmission_range(self, index1, index2):
        node1 = self.node_int_xy_dict[index1]
        node2 = self.node_int_xy_dict[index2]
        return self.dist_node_xy(node1, node2) <= self.transmission_range

    def is_within_interference_range(self, index1, index2):
        node1 = self.node_int_xy_dict[index1]
        node2 = self.node_int_xy_dict[index2]
        return self.dist_node_xy(node1, node2) <= self.interference_range

    def rotate_point(self, origin, point, angle):
        (ox, oy) = origin
        (px, py) = point
        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return (qx, qy)

    def get_line_width(self, line_style):
        if line_style == "solid":
            return 15.5
        return 3

    def draw_and_save_edges(self, single_edges, double_edges, triple_edges, file_name, list_ellipsoids=[], nodesize=15000):
        import matplotlib.pyplot as plt
        from matplotlib import pylab
        plt.figure(num=None, figsize=(20 * 2, 20 * 2), dpi=180)
        plt.axis('off')
        fig = plt.figure(1)
        nx.draw_networkx_nodes(self.G, self.pos, nodelist=self.G.nodes(),
                               node_color='black', node_size=nodesize, alpha=1, linewidths=4)
        nx.draw_networkx_labels(self.G, self.pos, labels=self.node_labels, with_labels=True, font_color="white", font_size=42)

        for li in single_edges:
            virtual_pos = {}
            virtual_edges = []
            src_xy, dst_xy = self.node_int_xy_dict[li[0]], self.node_int_xy_dict[li[1]]
            x1, y1, x2, y2 = src_xy[0], src_xy[1], dst_xy[0], dst_xy[1]
            node1_for_e1 = (x1, y1)
            node2_for_e1 = (x2, y2)
            virtual_edges.append((node1_for_e1, node2_for_e1))
            virtual_pos[node1_for_e1] = node1_for_e1
            virtual_pos[node2_for_e1] = node2_for_e1
            color = li[2]
            line_style = li[3]
            nx.draw_networkx_edges(self.G, virtual_pos, edgelist=virtual_edges,
                                   edge_color=color, width=self.get_line_width(line_style), style=line_style)

        for li in double_edges:
            virtual_pos = {}
            virtual_edges_1 = []
            virtual_edges_2 = []
            src_xy, dst_xy = self.node_int_xy_dict[li[0]], self.node_int_xy_dict[li[1]]
            x1, y1, x2, y2 = src_xy[0], src_xy[1], dst_xy[0], dst_xy[1]
            color_1 = li[2]
            color_2 = li[3]
            line_style_1 = li[4]
            line_style_2 = li[5]
            _vertical_verctor = (y2 - y1, x1 - x2)
            length_verctor = math.sqrt((y2 - y1) ** 2 + (x1 - x2) ** 2)
            virtual_vector = (_vertical_verctor[0] / length_verctor,
                                _vertical_verctor[1] / length_verctor)
            d = 0.15
            node1_for_e1 = (x1 + d * virtual_vector[0], y1 + d * virtual_vector[1])
            node2_for_e1 = (x2 + d * virtual_vector[0], y2 + d * virtual_vector[1])
            node1_for_e2 = (x1 - d * virtual_vector[0], y1 - d * virtual_vector[1])
            node2_for_e2 = (x2 - d * virtual_vector[0], y2 - d * virtual_vector[1])
            virtual_edges_1.append((node1_for_e1, node2_for_e1))
            virtual_edges_2.append((node1_for_e2, node2_for_e2))
            virtual_pos[node1_for_e1] = node1_for_e1
            virtual_pos[node2_for_e1] = node2_for_e1
            virtual_pos[node1_for_e2] = node1_for_e2
            virtual_pos[node2_for_e2] = node2_for_e2
            nx.draw_networkx_edges(self.G, virtual_pos, edgelist=virtual_edges_1,
                                   edge_color=color_1, width=self.get_line_width(line_style_1), style=line_style_1)
            nx.draw_networkx_edges(self.G, virtual_pos, edgelist=virtual_edges_2,
                                   edge_color=color_2, width=self.get_line_width(line_style_2), style=line_style_2)

        for li in triple_edges:
            virtual_pos = {}
            virtual_edges_1 = []
            virtual_edges_2 = []
            virtual_edges_3 = []
            src_xy, dst_xy = self.node_int_xy_dict[li[0]], self.node_int_xy_dict[li[1]]
            x1, y1, x2, y2 = src_xy[0], src_xy[1], dst_xy[0], dst_xy[1]
            color_1 = li[2]
            color_2 = li[3]
            color_3 = li[4]
            line_style_1 = li[5]
            line_style_2 = li[6]
            line_style_3 = li[7]
            _vertical_verctor = (y2 - y1, x1 - x2)
            length_verctor = math.sqrt((y2 - y1) ** 2 + (x1 - x2) ** 2)
            virtual_vector = (_vertical_verctor[0] / length_verctor,
                             _vertical_verctor[1] / length_verctor)
            d = 0.15
            node1_for_e1 = (x1 + d * virtual_vector[0], y1 + d * virtual_vector[1])
            node2_for_e1 = (x2 + d * virtual_vector[0], y2 + d * virtual_vector[1])
            node1_for_e2 = (x1 - d * virtual_vector[0], y1 - d * virtual_vector[1])
            node2_for_e2 = (x2 - d * virtual_vector[0], y2 - d * virtual_vector[1])
            node1_for_e3 = (x1, y1)
            node2_for_e3 = (x2, y2)
            virtual_edges_1.append((node1_for_e1, node2_for_e1))
            virtual_edges_2.append((node1_for_e2, node2_for_e2))
            virtual_edges_3.append((node1_for_e3, node2_for_e3))
            virtual_pos[node1_for_e1] = node1_for_e1
            virtual_pos[node2_for_e1] = node2_for_e1
            virtual_pos[node1_for_e2] = node1_for_e2
            virtual_pos[node2_for_e2] = node2_for_e2
            virtual_pos[node1_for_e3] = node1_for_e3
            virtual_pos[node2_for_e3] = node2_for_e3
            nx.draw_networkx_edges(self.G, virtual_pos, edgelist=virtual_edges_1,
                                   edge_color=color_1, width=self.get_line_width(line_style_1), style=line_style_1)
            nx.draw_networkx_edges(self.G, virtual_pos, edgelist=virtual_edges_2,
                                   edge_color=color_2, width=self.get_line_width(line_style_2), style=line_style_2)
            nx.draw_networkx_edges(self.G, virtual_pos, edgelist=virtual_edges_3,
                                   edge_color=color_3, width=self.get_line_width(line_style_3), style=line_style_3)

        for elli in list_ellipsoids:
            plt.gcf().gca().add_artist(elli)

        cut = 1.00
        xmax = cut * max(xx for xx, yy in self.pos.values())
        ymax = cut * max(yy for xx, yy in self.pos.values())
        plt.xlim(-2, xmax + 2)
        plt.ylim(-2, ymax + 2)
        plt.savefig(file_name, bbox_inches="tight")
        plt.close(fig)
        plt.close("all")
        pylab.close()
        del fig

if __name__ == "__main__":
    '''
    Note:
    20 nodes 60 links 7 channels: transmission_range = 8, interference_range = 12, xylimit = 18
    50 nodes 150 links 7 channels: transmission_range = 8, interference_range = 12, xylimit = 25
    '''
    for i in range(3):
        try:
            while 1:
                gm = GraphModel(number_nodes=20,
                                number_links_transmission=60,
                                number_extra_conflict_link_pairs=20,
                                number_of_channels=7,
                                min_number_link_of_each_channel=6,
                                max_number_link_of_each_channel=10,
                                transmission_range=8,
                                interference_range=14,
                                transmission_connection_ratio=0.9,
                                xylimit=20, file_type=".png")
                if gm.check_is_constructed():
                    break
            gm.illustrate()
            # gm.save()
        except Exception:
            continue

