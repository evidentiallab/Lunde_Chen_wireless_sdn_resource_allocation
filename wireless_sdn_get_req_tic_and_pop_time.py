from __future__ import print_function
import dill


def load_req_tasks(file_name_pickle):
    with open(file_name_pickle, 'rb') as f:
        return dill.load(f)


class RestoreReqListsTicPopTime(object):
    def __init__(self, req_tasks):
        self.str_time = req_tasks.str_time
        self.number_nodes = req_tasks.number_nodes
        self.path_split_ratio = req_tasks.path_split_ratio
        self.param_poisson = req_tasks.param_poisson
        self.param_exponential = req_tasks.param_exponential
        self.time_max = req_tasks.time_max
        self.finished = False
        self.hd = req_tasks.hd

        self.list_tic_new_requests = []
        self.list_pop_time  = []

        self.json_to_pickle = {0: self.list_tic_new_requests, 1: self.list_pop_time, 2: self.time_max, 3: self.param_poisson}

    def restore_list_tic_new_requests_and_pop_time(self):
        while len(self.hd):
            (_time, (_t, task)) = self.hd.popitem()
            if task.flag_new_requests:
                self.list_tic_new_requests.append(_time)
                self.list_pop_time.append(task.tuple_poptime_requests[0])

    def save(self):
        with open("0" + str(1000 + int(100 * self.param_poisson))[-2:] + '_lists_tic_pop_time', 'wb') as f:
            dill.dump(self.json_to_pickle, f)

    # see: https://stackoverflow.com/questions/2709800/how-to-pickle-yourself
    def load(self, obj):
        self.__dict__.update(dill.loads(obj).__dict__)


if __name__ == "__main__":
    # import os
    # os.chdir("../wireless_resource_allocation")
    req_tasks = load_req_tasks("wireless_sdn_pickles/req_nodes_20_rate_002/1")
    m = RestoreReqListsTicPopTime(req_tasks)
    m.restore_list_tic_new_requests_and_pop_time()
    m.save()
