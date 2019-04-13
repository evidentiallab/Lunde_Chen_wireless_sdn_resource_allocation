from __future__ import print_function
from wireless_sdn_requests import RequestGenerator
import random
from wireless_sdn_heapdict import heapdict
import copy
from wireless_sdn_ilp import ResourceAllocationILP
from wireless_sdn_graph_model import GraphModel
import wireless_sdn_ga as genetic_algorithm
from wireless_sdn_requests import Task

class AppRandomMode(object):
    def __init__(self, graph_model, param_poisson=0.01, path_split_ratio=1, obj_fun_parameters=(1, 0.1, 0.1, 0.03)):
        self.file_name = graph_model.str_time + "_random_mode.txt"
        self.graph_model_for_requests_generator = copy.deepcopy(graph_model)
        self.graph_model_ilp = copy.deepcopy(graph_model)
        self.graph_model_ga  = copy.deepcopy(graph_model)
        self.graph_model_sph = copy.deepcopy(graph_model)
        self.path_split_ratio = path_split_ratio
        self.param_poisson = param_poisson  # 0.01
        self.param_exponential = 1000
        self.time_max     = 10000
        self.finished     = False
        self.obj_fun_parameters = obj_fun_parameters
        self.request_generator = RequestGenerator(self.graph_model_for_requests_generator.number_nodes, path_split_ratio=path_split_ratio)

        tic = 0
        list_tic_new_requests = [0]
        while True:
            tic += int(random.expovariate(self.param_poisson))
            if tic <= self.time_max:
                list_tic_new_requests.append(tic)
            else:
                break

        self.hd = heapdict()
        for t in list_tic_new_requests:
            task = Task()
            task.task_time = t
            task.flag_new_requests = True
            self.hd[t] = (t, task)

    def start(self):

        while len(self.hd):
            (_time, (_t, task)) = self.hd.popitem()
            current_time = task.task_time
            if _time != current_time or _time != _t:
                print("NOT EQUAL")
                return
            if current_time > self.time_max:
                break
            if task.flag_new_requests:
                life_time = int(random.expovariate(1.0000 / self.param_exponential))
                pop_time = current_time + life_time
                requests = self.request_generator.generate_requests(life_time, pop_time)
                resource_allocation_ilp = ResourceAllocationILP(
                    self.graph_model_ilp, obj_fun_parameters=self.obj_fun_parameters)

                flag_ilp, flag_ga = False, False
                try:
                    flag_ilp, res_ilp, resource_model_ilp = resource_allocation_ilp.main(
                        requests, time_limit=1200, mip_gap=0.02, flag_log=False)
                except:
                    pass

                try:
                    flag_ga, res_ga, resource_model_ga, _ = \
                        genetic_algorithm.main_with_static_link_cost(self.graph_model_ga,
                                               requests, NGEN=50, IND_SIZE=50,
                                               CXPB=0.9,
                                               MUTPB=0.1, CHAPB=0.9, n_process=1,
                                               obj_fun_parameters=self.obj_fun_parameters,
                                               dynamic_link_cost_mode=False)
                except:
                    pass

                (_, task_future) = self.hd.setdefault(pop_time, (pop_time, Task()))
                task_future.task_time = pop_time
                task_future.flag_expire_requests = True
                if flag_ilp:
                    task_future.expire_ilp.append(resource_model_ilp)
                if flag_ga:
                    task_future.expire_ga.append(resource_model_ga)

                fo = open(self.file_name, "a")
                fo.write("UT : " + str(current_time) + '\n')
                fo.write("ILP: " + str(flag_ilp) + '\n')
                fo.write("GA : " + str(flag_ga) + '\n')
                if flag_ilp:
                    fo.write("ILP: " + str(res_ilp) + '\n')
                if flag_ga:
                    fo.write("GA : " + str(res_ga) + '\n')
                if flag_ilp:
                    fo.write("ILP: " + str(resource_model_ilp) + '\n')
                if flag_ga:
                    fo.write("GA : " + str(resource_model_ga) + '\n')
                fo.write("-----------------------------\n")
                fo.close()

                if flag_ilp:
                    self.graph_model_ilp.consume_resource(resource_model_ilp)
                if flag_ga:
                    self.graph_model_ga.consume_resource(resource_model_ga)

            if task.flag_expire_requests:
                for resource_expire_ilp in task.expire_ilp:
                    self.graph_model_ilp.recover_resource(resource_expire_ilp)
                for resource_expire_ga in task.expire_ga:
                    self.graph_model_ga.recover_resource(resource_expire_ga)

if __name__ == "__main__":
    i = 0
    while True:
        if i >= 30:
            break
        try:
            while 1:
                gm = GraphModel(number_nodes=20,
                                number_links_transmission=60,
                                number_extra_conflict_link_pairs=0,
                                number_of_cliques_min=4,
                                number_of_cliques_max=17,
                                number_of_channels=3,
                                min_number_link_of_each_channel=3,
                                max_number_link_of_each_channel=50,
                                transmission_range=6,
                                interference_range=10,
                                transmission_connection_ratio=0.9,
                                json_channels={1: {"color": "violet", "capacity": 100},
                                               2: {"color": "blue", "capacity": 100},
                                               3: {"color": "orange", "capacity": 100},
                                               4: {"color": "green", "capacity": 100},
                                               5: {"color": "yellow", "capacity": 100},
                                               6: {"color": "red", "capacity": 100},
                                               7: {"color": "gray", "capacity": 100},
                                               },
                                number_of_openflow_entries=10000, number_of_group_entries=2000,
                                xylimit=18, file_type=".png")
                if gm.check_is_constructed():
                    break
            app = AppRandomMode(gm, param_poisson=0.06, path_split_ratio=1,  obj_fun_parameters=(1, 0.0, 0.0, 0.1))
            app.start()
            i += 1
        except Exception:
            continue

