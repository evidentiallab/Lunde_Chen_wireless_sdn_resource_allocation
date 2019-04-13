from __future__ import print_function
import dill


def load_graph_model(file_name_pickle):
    with open(file_name_pickle, 'rb') as f:
        return dill.load(f)

def load_req_tasks(file_name_pickle):
    with open(file_name_pickle, 'rb') as f:
        return dill.load(f)


def reset_resource(graph_model, bw_residu, openflow_entries_residu, group_entries_residu):
    if bw_residu != -1:
        for link_id in range(1, graph_model.number_links_transmission + 1):
            graph_model.bw_info_dict[link_id].bw_residu = bw_residu
        for clique_id, _ in graph_model.dict_clique_id_residual_capacity.items():
            graph_model.dict_clique_id_residual_capacity[clique_id] = bw_residu
        for ch, _ in graph_model.json_channels.items():
            graph_model.json_channels[ch]['capacity'] = bw_residu
    if openflow_entries_residu != -1:
        graph_model.number_of_openflow_entries = openflow_entries_residu
        for node_id in range(1, graph_model.number_nodes + 1):
            graph_model.of_table_info_dict[node_id].openflow_entries_residu = openflow_entries_residu
    if group_entries_residu != -1:
        graph_model.number_of_group_entries = group_entries_residu
        for node_id in range(1, graph_model.number_nodes + 1):
            graph_model.of_table_info_dict[node_id].group_entries_residu = group_entries_residu


def consume_resource_backup(graph_model, resource_model, flag_consume=True):
    neg = 1
    if not flag_consume:
        neg *= -1
    for link_id, capacity_decrease in resource_model.dict_link_id_total_capacity_decrease.items():
        graph_model.bw_info_dict[link_id].bw_residu -= int(neg * capacity_decrease)
    for node_id, openflow_table_decrease in resource_model.dict_node_id_openflow_table_decrease.items():
        graph_model.of_table_info_dict[node_id].openflow_entries_residu -= neg * openflow_table_decrease
    for node_id, group_table_decrease in resource_model.dict_node_id_group_table_decrease.items():
        graph_model.of_table_info_dict[node_id].group_entries_residu -= neg * group_table_decrease


def consume_resource(graph_model, resource_model, flag_consume=True):
    neg = 1
    if not flag_consume:
        neg *= -1
    for link_id, bw_consumption in resource_model.dict_link_id_total_bw_consumption.items():
        for clique_id in graph_model.dict_link_clique_id[link_id]:
            graph_model.dict_clique_id_residual_capacity[clique_id] -= int(neg * bw_consumption)
    for node_id, openflow_table_decrease in resource_model.dict_node_id_openflow_table_decrease.items():
        graph_model.of_table_info_dict[node_id].openflow_entries_residu -= neg * openflow_table_decrease
    for node_id, group_table_decrease in resource_model.dict_node_id_group_table_decrease.items():
        graph_model.of_table_info_dict[node_id].group_entries_residu -= neg * group_table_decrease


def recover_resource(graph_model, resource_model):
    consume_resource(graph_model, resource_model, flag_consume=False)


if __name__ == "__main__":
    # gm = load_graph_model("wireless_sdn_pickles/network_model_1/1")
    gm = load_graph_model("wireless_sdn_pickles/network_model_98/1")
    # req_tasks = load_req_tasks("wireless_sdn_pickles/req_nodes_20_rate_002/1")
