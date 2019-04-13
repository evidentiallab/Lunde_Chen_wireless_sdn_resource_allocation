from __future__ import print_function
from wireless_sdn_graph_model import GraphModel
from wireless_sdn_requests import Request
from wireless_sdn_ilp import ResourceAllocationILP, ResourceAllocationNoMulticastAdvantageILP
import wireless_sdn_replay_helper as replay
from wireless_sdn_requests import Task
import wireless_sdn_utils as utils
import time


def main_test():
    sw_openflow = 20000
    sw_group = 20000
    obj_fun_parameters = (1, 0, 0, 0.6)

    req = Request()
    req.request_id = 1
    req.src = 7
    req.list_dst = [4, 8, 9]
    req.request_bw = 10
    req.number_dst = len(req.list_dst)
    req.delay_max = 1000
    req.allow_multi_links = True
    req.path_split_ratio = 0
    requests = [req]

    gm = replay.load_graph_model("wireless_sdn_pickles/network_model_10/" + "2")
    replay.reset_resource(gm, -1, sw_openflow, sw_group)

    resource_allocation_ilp = ResourceAllocationILP(gm, obj_fun_parameters=obj_fun_parameters)

    try:
        flag_ilp, res_ilp, resource_model_ilp = resource_allocation_ilp.main(
            requests, time_limit=5, mip_gap=0.01, flag_log=True)
        print(str(resource_model_ilp))
    except Exception:
        pass

    time.sleep(0.5)
    resource_allocation_ilp_no_multicast_advantage = \
        ResourceAllocationNoMulticastAdvantageILP(gm, obj_fun_parameters=obj_fun_parameters)
    try:
        flag_ilp, res_ilp, resource_model_ilp = resource_allocation_ilp_no_multicast_advantage.main(
            requests, time_limit=5, mip_gap=0.01, flag_log=True)
        print(str(resource_model_ilp))
    except Exception:
        pass


if __name__ == "__main__":
    main_test()


