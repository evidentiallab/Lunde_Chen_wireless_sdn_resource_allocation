# coding: utf-8
from __future__ import print_function
from wireless_sdn_graph_model import GraphModel
import wireless_sdn_replay_helper
import copy


class GraphModelModifyPickle(GraphModel):
    def __init__(self,  file_name_new_plot_figure):
        GraphModel.__init__(self)
        self.file_name_pickle = './modify_pickle/1'
        self.file_name_new_plot_figure = './modify_pickle/' + file_name_new_plot_figure
        self.gm = wireless_sdn_replay_helper.load_graph_model(self.file_name_pickle)
        self.xlimit = self.gm.xlimit
        self.ylimit = self.gm.ylimit
        self.file_type = self.gm.file_type
        self.number_nodes = self.gm.number_nodes
        self.number_of_cliques_min = self.gm.number_of_cliques_min
        self.number_of_cliques_max = self.gm.number_of_cliques_max
        self.transmission_connection_ratio = self.gm.transmission_connection_ratio
        self.transmission_range = self.gm.transmission_range
        self.interference_range = self.gm.interference_range
        self.number_of_openflow_entries = self.gm.number_of_openflow_entries
        self.number_of_group_entries = self.gm.number_of_group_entries
        self.json_channels = self.gm.json_channels
        self.list_channels = self.gm.list_channels
        self.set_channels_used = self.gm.set_channels_used
        self.number_channels = self.gm.number_channels
        self.channel_info_dict = self.gm.channel_info_dict
        self.shared_trans_link_channel_info_dict = self.gm.shared_trans_link_channel_info_dict
        self.bw_info_dict = self.gm.bw_info_dict
        self.of_table_info_dict = self.gm.of_table_info_dict
        self.multi_link_info_dict = self.gm.multi_link_info_dict
        self.multi_link_keys_set = self.gm.multi_link_keys_set
        self.multi_link_link_id_set = self.gm.multi_link_link_id_set
        self.transmission_int_link_key_dict = self.gm.transmission_int_link_key_dict
        self.str_time = self.file_name_new_plot_figure
        self.G = self.gm.G
        self.G_int = self.gm.G_int
        self.node_int_xy_dict = self.gm.node_int_xy_dict
        self.node_xy_int_dict = self.gm.node_xy_int_dict
        self.node_int_node_instance_dict = self.gm.node_int_node_instance_dict
        self.is_connected = self.gm.is_connected
        self.is_constructed = self.gm.is_constructed
        self.node_labels = self.gm.node_labels
        self.number_links_transmission = self.gm.number_links_transmission
        self.number_extra_conflict_link_pairs = self.gm.number_extra_conflict_link_pairs
        self.dict_channel_conflict_links = self.gm.dict_channel_conflict_links
        self.dict_channel_cliques = self.gm.dict_channel_cliques
        self.all_cliques = self.gm.all_cliques
        self.clique_id = self.gm.clique_id
        self.dict_link_clique_id = self.gm.dict_link_clique_id
        self.dict_clique_id_residual_capacity = self.gm.dict_clique_id_residual_capacity
        self.dict_clique_id_clique = self.gm.dict_clique_id_clique
        self.int_link_illustration_dict = self.gm.int_link_illustration_dict
        self.int_link_transmission_dict = self.gm.int_link_transmission_dict
        self.pos = self.gm.pos
        self.dict_interference_pair_info = self.gm.dict_interference_pair_info
        self.node_int_xy_dict_old = copy.deepcopy(self.node_int_xy_dict)
        self.clique_based = False

    def modify_node_pos(self, node_id, dx, dy):
        (x, y) = self.node_int_xy_dict[node_id]
        new_xy = (x + dx, y + dy)
        self.node_int_xy_dict[node_id] = new_xy
        self.pos[self.node_int_xy_dict_old[node_id]] = new_xy

    def modify_node_label(self, dict_of_label_change_scheme):
        for node, old_label in self.node_labels.items():
            self.node_labels[node] = dict_of_label_change_scheme[old_label]


def modify_network_model_1():
    mp = GraphModelModifyPickle('1mm')
    mp.modify_node_pos(3, 4, -1.5)
    mp.modify_node_pos(2, -1.8, 0)
    mp.modify_node_pos(17, -1, 0)
    mp.modify_node_pos(5, -0.0, 4.3)
    mp.modify_node_pos(1, 1.5, -1)
    mp.modify_node_pos(6, 3, 0.5)
    mp.modify_node_pos(7, -0.3, -3.3)
    mp.modify_node_pos(9, -0.3, -1.0)
    mp.modify_node_pos(20, 2.9, -1.5)
    mp.modify_node_pos(14, 1, 0)
    mp.modify_node_pos(13, -2, -0.5)
    mp.modify_node_pos(11, 1.0, 0)
    mp.modify_node_pos(15, 2, -0.5)
    mp.modify_node_pos(12, -8.5, -4.9)
    mp.modify_node_pos(16, 3, 0)
    mp.modify_node_pos(18, 2, 1)
    mp.modify_node_pos(19, -2, 1.5)
    mp.modify_node_pos(8, -1, -1)
    mp.modify_node_pos(10, 0.6, 0)
    dict_of_label_change_scheme = {}
    n = 1
    for i in [14, 3, 18, 20, 11, 9, 6, 15, 5, 1, 4, 16, 10, 2, 7, 12, 17, 19, 13, 8]:
        dict_of_label_change_scheme[i] = n
        n += 1
    mp.modify_node_label(dict_of_label_change_scheme)
    mp.illustrate()
    mp.save()
    print("Hello Toulouse")


if __name__ == "__main__":
    modify_network_model_1()

