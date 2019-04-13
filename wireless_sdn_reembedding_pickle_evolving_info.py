from __future__ import print_function
import random
import dill
import wireless_sdn_replay_helper
import copy


def generate_time_points_to_evolve():
    req_tasks = wireless_sdn_replay_helper.load_req_tasks("wireless_sdn_pickles/req_nodes_20_rate_002/1")
    hd = req_tasks.hd

    time_points_new_request = []

    while len(hd):
        (_time, (_t, task)) = hd.popitem()
        current_time = task.task_time
        if _time != current_time or _time != _t:
            print("NOT EQUAL")
            return

        if _time > req_tasks.time_max:
            break

        if task.flag_new_requests:
            time_points_new_request.append(_time)

    seed = 70
    evolving_ratio = 0.3
    random.seed(seed)
    time_points_to_evolve = sorted(random.sample(time_points_new_request, int(len(time_points_new_request) * evolving_ratio)))
    return time_points_to_evolve


def pickle_evolving_add_destinations():
    evolving_info = dict()
    req_tasks = wireless_sdn_replay_helper.load_req_tasks("wireless_sdn_pickles/req_nodes_20_rate_002/1")
    hd = req_tasks.hd
    time_points_to_evolve = generate_time_points_to_evolve()

    while len(hd):
        (_time, (_t, task)) = hd.popitem()
        current_time = task.task_time
        if _time != current_time or _time != _t:
            print("NOT EQUAL")
            return

        if _time > req_tasks.time_max:
            break

        if task.flag_new_requests:
            (pop_time, requests) = task.tuple_poptime_requests
            if _time in time_points_to_evolve:
                new_requests = []
                for req in requests:
                    new_req = copy.deepcopy(req)
                    src = req.src
                    list_dst = req.list_dst
                    sample_pool = []
                    for i in range(1, 21):
                        if i not in [src] + list_dst:
                            sample_pool.append(i)
                    new_req.list_dst += random.sample(sample_pool, random.randint(1, 4))
                    new_req.number_dst = len(new_req.list_dst)
                    new_requests.append(new_req)
                evolving_info[_time] = new_requests

    with open("wireless_sdn_pickles/req_nodes_20_rate_002/1_evolving_add_nodes", 'wb') as f:
        dill.dump(evolving_info, f)


def pickle_evolving_increase_bandwidth():
    evolving_info = dict()
    req_tasks = wireless_sdn_replay_helper.load_req_tasks("wireless_sdn_pickles/req_nodes_20_rate_002/1")
    hd = req_tasks.hd
    time_points_to_evolve = generate_time_points_to_evolve()

    while len(hd):
        (_time, (_t, task)) = hd.popitem()
        current_time = task.task_time
        if _time != current_time or _time != _t:
            print("NOT EQUAL")
            return

        if _time > req_tasks.time_max:
            break

        if task.flag_new_requests:
            (pop_time, requests) = task.tuple_poptime_requests
            if _time in time_points_to_evolve:
                new_requests = []
                for req in requests:
                    new_req = copy.deepcopy(req)

                    request_bw = req.request_bw
                    new_req.request_bw = request_bw + random.randint(1, 4)

                    new_requests.append(new_req)
                evolving_info[_time] = new_requests

    with open("wireless_sdn_pickles/req_nodes_20_rate_002/1_evolving_increase_bandwidth", 'wb') as f:
        dill.dump(evolving_info, f)


if __name__ == '__main__':
    pickle_evolving_add_destinations()
    pickle_evolving_increase_bandwidth()

    req_tasks_evolving_add_destinations = wireless_sdn_replay_helper.load_req_tasks("wireless_sdn_pickles/req_nodes_20_rate_002/1_evolving_add_nodes")
    req_tasks_evolving_increase_bandwidth = wireless_sdn_replay_helper.load_req_tasks("wireless_sdn_pickles/req_nodes_20_rate_002/1_evolving_increase_bandwidth")

    print("Hello Toulouse")

