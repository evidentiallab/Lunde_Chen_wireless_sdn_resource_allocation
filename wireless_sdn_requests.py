from random import randint
import random

class Task(object):
    def __init__(self):
        self.task_time = -1
        self.flag_new_requests = False
        self.tuple_poptime_requests = ()

        self.flag_expire_requests = False
        self.expire_ilp = []
        self.expire_ga  = []
        self.expire_sph = []

class Request(object):
    def __init__(self):
        self.request_id = -1
        self.src        = None
        self.list_dst   = None
        self.request_bw = -1
        self.number_dst = -1
        self.allow_multi_links = True
        self.path_split_ratio  = 0.5
        self.life_time         = -1
        self.pop_time          = -1

class RequestGenerator(object):
    def __init__(self, number_nodes, path_split_ratio=1):
        self.number_nodes = number_nodes
        self.count        = 0
        self.path_split_ratio = path_split_ratio

    def generate_one_request(self, k, life_time, pop_time):
        req = Request()
        req.request_id = k
        req.src = randint(1, self.number_nodes)
        _list_dst = [req.src]
        while 1:
            if req.src not in _list_dst:
                break
            _list_dst = random.sample(range(1, self.number_nodes + 1), randint(1, 5))
        req.list_dst = _list_dst[:]
        req.request_bw = random.choice([1, 2, 3])
        req.number_dst = len(req.list_dst)
        req.allow_multi_links = True
        req.path_split_ratio  = self.path_split_ratio
        req.life_time = life_time
        req.pop_time = pop_time
        return req

    def generate_requests(self, life_time, pop_time):
        number_of_vlinks = random.choice([4, 6])
        requests = []
        for k in range(self.count, self.count + number_of_vlinks):
            requests.append(self.generate_one_request(k, life_time, pop_time))
        self.count += number_of_vlinks
        return requests

