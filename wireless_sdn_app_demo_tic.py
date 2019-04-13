from __future__ import print_function
import random
from wireless_sdn_heapdict import heapdict


class TaskDemo(object):
    def __init__(self):
        self.task_time = -1
        self.flag_new_requests = False
        self.flag_expire_requests = False
        self.list_expire_requests = []


class ApplicationDicDemo(object):
    def __init__(self, param_poisson=0.04):
        self.param_poisson = param_poisson  # 0.04 or 0.10
        self.param_exponential = 1000
        self.time_max     = 10000
        self.finished     = False

        tic = 0
        list_tic_new_requests = [0]
        while True:
            tic += int(random.expovariate(self.param_poisson))
            if tic <= self.time_max:
                list_tic_new_requests.append(tic)
            else:
                break

        self.hq = heapdict()
        for t in list_tic_new_requests:
            task = TaskDemo()
            task.task_time = t
            task.flag_new_requests = True
            self.hq[t] = (t, task)

    def start(self):
        while len(self.hq):
            (_time, (_t, task)) = self.hq.popitem()
            current_time = task.task_time
            if _time != current_time or _time != _t:
                print("NOT EQUAL")
                return
            if current_time > self.time_max:
                break
            if task.flag_new_requests:
                life_time = int(random.expovariate(1.0000 / self.param_exponential))
                pop_time = current_time + life_time
                requests = "Request " + str(current_time) + " --> " + str(pop_time)
                (_, task_future) = self.hq.setdefault(pop_time, (pop_time, TaskDemo()))
                task_future.task_time = pop_time
                task_future.flag_expire_requests = True
                task_future.list_expire_requests.append(requests)
                print(str(current_time), " : ", requests,  " ADDED")
            if task.flag_expire_requests:
                for expire_request in task.list_expire_requests:
                    print(str(current_time), " : ", expire_request, " EXPIRED")

if __name__ == "__main__":
    app = ApplicationDicDemo(param_poisson=0.04)
    app.start()

