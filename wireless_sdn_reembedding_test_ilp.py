from wireless_sdn_graph_model import GraphModel
from wireless_sdn_requests import Request
from wireless_sdn_ilp import ResourceAllocationILP
from wireless_sdn_replay_helper import load_graph_model
from wireless_sdn_replay_helper import load_req_tasks
from wireless_sdn_reembedding_ilp import ReEmbeddingILP


def test_with_6_nodes():
    try:
        gm = load_graph_model("wireless_sdn_pickles/network_model_98/1")

        old_req = Request()
        old_req.request_id = 1
        old_req.src = 6
        old_req.list_dst = [2, 3]
        old_req.request_bw = 88
        old_req.number_dst = len(old_req.list_dst)
        old_req.delay_max = 1000
        old_req.allow_multi_links = True
        old_req.path_split_ratio = 0
        old_requests = [old_req]

        new_req = Request()
        new_req.request_id = 1
        new_req.src = 6
        new_req.list_dst = [2, 3, 8]
        new_req.request_bw = 99
        new_req.number_dst = len(new_req.list_dst)
        new_req.delay_max = 1000
        new_req.allow_multi_links = True
        new_req.path_split_ratio = 0
        new_requests = [new_req]

        resource_reallocation = ReEmbeddingILP(gm)
        resource_reallocation.embed_and_then_reembed(old_requests, new_requests, flag_log=True)

    except Exception:
        pass


if __name__ == '__main__':
    test_with_6_nodes()


