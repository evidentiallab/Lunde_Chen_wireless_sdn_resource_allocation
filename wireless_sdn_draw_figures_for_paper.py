import networkx as nx
from random import randint
import matplotlib.pyplot as plt
from matplotlib import pylab
import math
import random
from matplotlib.patches import Ellipse
import numpy as np
import wireless_sdn_utils
from wireless_sdn_network_info import *
import time
from datetime import datetime

class GraphModelDrawForPaper(object):
    def __init__(self,
                 json_channels={1: {"color": "violet", "capacity": 1024},
                                2: {"color": "blue", "capacity": 1024},
                                3: {"color": "orange", "capacity": 1024},
                                # 4: {"color": "green", "capacity": 1024}
                                }, xlimit=18, ylimit=18, file_type=".png"):
        ''' 
        '''
        # TODO Save good results of graph models to pickles or json
        self.xlimit = xlimit
        self.ylimit = ylimit
        self.json_channels = json_channels
        self.list_channels = sorted(json_channels.keys())
        self.number_channels = len(self.list_channels)
        self.transmission_int_link_key_dict  = {}
        self.str_time = time.strftime("0_illustr_%Y%m%d%H%M%S") + str(int(int(datetime.utcnow().strftime('%f')) / 1000))
        self.G = nx.Graph()
        self.G_int = nx.Graph()
        self.node_int_xy_dict = {}
        self.node_xy_int_dict = {}
        self.node_int_node_instance_dict = {}
        self.channel_info_dict = {ch: ChannelInfo(ch) for ch in self.list_channels}
        self.is_connected = True
        self.node_labels = {}
        self.file_type = file_type

        dict_nodes_pos = {2: (2, 10.5), 7: (2.3, 7.1), 1: (6, 6.8), 5: (10, 7), 3: (12.8, 6), 6: (14, 10), 8: (8, 11), 4: (5, 13)}
        # list_transmission_link_violet = [(2, 7), (6, 8), (5, 8), (3, 5), (5, 6)]
        # list_transmission_link_blue = [(1, 7), (1, 8), (4, 8), (1, 5), (3, 5)]
        # list_transmission_link_orange = [(2, 7), (2, 8), (1, 8), (5, 6)]
        # list_interference_link_violet = [(3, 6)]
        # list_interference_link_blue = [(1, 3)]
        # list_interference_link_orange = [(1, 2)]

        list_transmission_link_violet = [(2, 7), (6, 8), (5, 8), (3, 5), (5, 6)]
        list_transmission_link_blue = [(1, 7), (1, 8), (4, 8), (1, 5), (3, 5)]
        list_transmission_link_orange = [(2, 7), (2, 8), (1, 8), (5, 6)]
        #
        # list_interference_link_violet = [(3, 6), (3, 8)]
        # list_interference_link_blue = [(1, 3), (4, 7), (1, 4), (5, 8), (3, 8), (5, 7)]
        # list_interference_link_orange = [(1, 2), (7, 8), (1, 7)]

        list_interference_link_violet = []
        list_interference_link_blue = []
        list_interference_link_orange = []

        self.number_nodes = len(dict_nodes_pos)
        list_nodes = []
        for _count, xy in dict_nodes_pos.iteritems():
            self.G.add_node(xy)
            self.G_int.add_node(_count)
            self.node_int_xy_dict[_count] = xy
            self.node_xy_int_dict[xy] = _count
            node = Node()
            node.index = _count
            node.xy = xy
            self.node_int_node_instance_dict[_count] = node
            self.node_labels[xy] = _count
            list_nodes.append(xy)

        node_channel_dict_tmp  = {}
        for i, xy in self.node_int_xy_dict.iteritems():
            # channels = sorted(random.sample(self.list_channels, randint(1, self.number_channels)))
            '''
            We limit the number of channels each node could have to 3.
            '''
            channels = sorted(random.sample(self.list_channels, randint(1, min(3, self.number_channels))))
            node_channel_dict_tmp[i] = channels

        self.int_link_illustration_dict = {}
        self.int_link_transmission_dict = {}
        self.int_link_interference_dict = {}

        count = 0
        for k in range(len(self.list_channels)):
            ch = self.list_channels[k]
            list_trans_links = [list_transmission_link_violet,
                                list_transmission_link_blue, list_transmission_link_orange][k]
            for int_int_pair in list_trans_links:
                (i, j) = int_int_pair
                count += 1
                link = Link()
                link.index = count
                link.channel = ch
                link.src = i
                link.dst = j
                link.color     = self.json_channels.get(ch).get("color")

                link_transmission = LinkTransmission()
                link_transmission.get_attributes_from_link(link)
                link_illustration = LinkIllustration()
                link_illustration.get_attributes_from_link(link_transmission)

                self.int_link_illustration_dict[count] = link_illustration
                self.int_link_transmission_dict[count] = link_transmission
                self.node_int_node_instance_dict[i].links_illustration.setdefault(j, []).append(
                    link_illustration)
                self.node_int_node_instance_dict[i].links_transmission.setdefault(j, []).append(
                    link_transmission)

                self.transmission_int_link_key_dict[count] = (int_int_pair[0], int_int_pair[1])

                self.node_int_node_instance_dict[i].channels.add(ch)
                self.G.add_edge(self.node_int_xy_dict[i], self.node_int_xy_dict[j])
                self.G_int.add_edge(i, j)
                self.channel_info_dict[ch].nodes_set.add(i)
                self.channel_info_dict[ch].nodes_set.add(j)
                self.channel_info_dict[ch].links_set.add(link_transmission)
                self.channel_info_dict[ch].links_list.append(count)
                self.channel_info_dict[ch].tuples_set.add((i, j))

        for k in range(len(self.list_channels)):
            ch = self.list_channels[k]
            list_interf_links = [list_interference_link_violet,
                                list_interference_link_blue, list_interference_link_orange][k]
            for int_int_pair in list_interf_links:
                (i, j) = int_int_pair
                count += 1
                link = Link()
                link.index = count
                link.channel = ch
                link.src = i
                link.dst = j
                link.color = self.json_channels.get(ch).get("color")

                link_interference = LinkInterference()
                link_interference.get_attributes_from_link(link)
                link_illustration = LinkIllustration()
                link_illustration.get_attributes_from_link(link_interference)

                self.int_link_illustration_dict[count] = link_illustration
                self.int_link_interference_dict[count] = link_interference
                self.node_int_node_instance_dict[i].links_illustration.setdefault(j, []).append(
                    link_illustration)
                self.node_int_node_instance_dict[i].links_interference.setdefault(j, []).append(
                    link_interference)

                self.channel_info_dict[ch].nodes_set.add(i)
                self.channel_info_dict[ch].nodes_set.add(j)
                self.channel_info_dict[ch].links_set.add(link_interference)
                self.channel_info_dict[ch].links_list.append(count)
                self.channel_info_dict[ch].tuples_set.add((i, j))

        self.number_links_transmission = len(self.int_link_transmission_dict)
        self.number_links_interference = len(self.int_link_interference_dict)
        self.number_links_illustration = len(self.int_link_illustration_dict)
        self.list_interference_link_int = self.int_link_transmission_dict.keys()
        self.list_transmission_link_int = self.int_link_interference_dict.keys()
        self.pos = dict(zip(self.G, self.G))

    def build_conflict_graph_and_cliques(self, ch):
        CG = nx.Graph()
        list_ellipsoids = []
        channel_info = self.channel_info_dict[ch]
        color = self.json_channels.get(ch).get("color")

        links = sorted(list(channel_info.links_set))
        size = len(links)
        for i in range(size - 1):
            if links[i].index > self.number_links_transmission:
                continue
            for j in range(i, size):
                if links[j].index > self.number_links_transmission:
                    continue

                '''
                violet = [(2, 7), (6, 8), (5, 8), (3, 5), (5, 6)]  
                            1       2       3       4        5

                blue   = [(1, 7), (1, 8), (4, 8), (1, 5), (3, 5)] 
                            6        7       8       9       10

                orange = [(2, 7), (2, 8), (1, 8), (5, 6)] 
                            11      12      13      14
                '''
                # _no_conflict = [(8, 9), (6, 10)]
                _no_conflict = [(6, 10)]
                if (links[i].index, links[j].index) in _no_conflict or (links[j].index, links[i].index) in _no_conflict:
                    continue

                flag = False
                a, b = links[i].src, links[i].dst
                c, d = links[j].src, links[j].dst
                if a == c or a == d or b == c or b == d:
                    flag = True
                elif any(tuple(sorted(one_hop_link)) in channel_info.tuples_set for one_hop_link in [(a, c), (a, d), (b, c), (b, d)]):
                    flag = True
                if flag:
                    (x1, y1) = self.node_int_xy_dict[a]
                    (x2, y2) = self.node_int_xy_dict[b]
                    (x3, y3) = self.node_int_xy_dict[c]
                    (x4, y4) = self.node_int_xy_dict[d]
                    mid_1 = ((x1 + x2) / float(2), (y1 + y2) / float(2))
                    mid_2 = ((x3 + x4) / float(2), (y3 + y4) / float(2))
                    CG.add_edge(mid_1, mid_2)

        cliques = list(nx.find_cliques(CG)) # TODO

        for elli_points in cliques:
            '''
            Attention, only cliques with more than 2 nodes are drawn in the illustration file. 
            But in calculation, those 2-nodes cliques should also be included, 
            if they are not already included in a larger clique.
            Comment the two lines if you want to check its effect.
            '''
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
            elli = Ellipse(xy=center, width=w, height=h, angle=angle360, color=color, alpha=0.15)
            list_ellipsoids.append(elli)
        conflict_edges = []
        for e in CG.edges():
            conflict_edges.append((e[0], e[1], color, "solid"))
        return CG, list_ellipsoids, conflict_edges

    def illustrate(self):
        single_edges = []
        double_edges = []
        triple_edges = []
        for i in range(1, self.number_nodes + 1):
            node = self.node_int_node_instance_dict[i]
            for j, list_link_illustr in node.links_illustration.iteritems():
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
        for ch in self.list_channels:
            try:
                color = self.json_channels.get(ch).get("color")
                CG, list_ellipsoids, conflict_edges = self.build_conflict_graph_and_cliques(ch)
                for i in range(len(list_ellipsoids)):
                    file_name = self.str_time + "_cliques_ch_" + color + "elli_" + str(i) + self.file_type
                    # self.draw_and_save_edges(single_edges, double_edges, triple_edges, file_name, list_ellipsoids=[list_ellipsoids[i]])
                all_ellipsoids += list_ellipsoids
            except Exception:
                continue
        file_name = self.str_time + "_cliques_all" + self.file_type
        self.draw_and_save_edges(single_edges, double_edges, triple_edges, file_name, list_ellipsoids=all_ellipsoids)

    def illustrate_white_links(self):
        '''
        violet = [(2, 7), (6, 8), (5, 8), (3, 5), (5, 6)]  
                    1       2       3       4        5
                    
        blue   = [(1, 7), (1, 8), (4, 8), (1, 5), (3, 5)] 
                    6        7       8       9       10
                    
        orange = [(2, 7), (2, 8), (1, 8), (5, 6)] 
                    11      12      13      14
        '''
        # non_white_links = [8, 13, 9]
        non_white_links = [8, 3, 12, 13, 6]
        single_edges = []
        double_edges = []
        triple_edges = []
        for _int, illustr_link in self.int_link_illustration_dict.items():
            if illustr_link.index not in non_white_links:
                illustr_link.color = "white"
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
        file_name = self.str_time + "_white_lines" + self.file_type
        self.draw_and_save_edges(single_edges, double_edges, triple_edges, file_name, list_ellipsoids=[])

    def rotate_point(self, origin, point, angle):
        (ox, oy) = origin
        (px, py) = point
        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return (qx, qy)

    def get_line_width(self, line_style):
        if line_style == "solid":
            return 15.5
        return 7

    def draw_and_save_edges(self, single_edges, double_edges, triple_edges, file_name, list_ellipsoids=[], nodesize=15000):
        plt.figure(num=None, figsize=(20 * 2, 20 * 2), dpi=280)
        plt.axis('off')
        fig = plt.figure(1)
        nx.draw_networkx_nodes(self.G, self.pos, nodelist=self.G.nodes(),
                               node_color='white', node_size=nodesize, alpha=1, linewidths=4)
        nx.draw_networkx_labels(self.G, self.pos, labels=self.node_labels, with_labels=True, font_color="black", font_size=48)

        for li in single_edges:
            src_xy, dst_xy = self.node_int_xy_dict[li[0]], self.node_int_xy_dict[li[1]]
            x1, y1, x2, y2 = src_xy[0], src_xy[1], dst_xy[0], dst_xy[1]
            edge_list = [((x1, y1), (x2, y2))]
            color     = li[2]
            line_style = li[3]
            nx.draw_networkx_edges(self.G, self.pos, edgelist=edge_list,
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
    gm = GraphModelDrawForPaper(file_type=".png")
    gm.illustrate()
    gm.illustrate_white_links()
