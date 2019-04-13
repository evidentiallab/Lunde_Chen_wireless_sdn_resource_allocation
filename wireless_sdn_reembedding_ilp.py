from __future__ import print_function
from wireless_sdn_ilp import ResourceAllocationILP
import time
from datetime import datetime
import cplex
from cplex.exceptions import CplexSolverError
from wireless_sdn_variable_model import *
from wireless_sdn_graph_model import ResourceModel


class ReEmbeddingILP(ResourceAllocationILP):
    def __init__(self, graph_model, coefficient_reembedding=10000, obj_fun_parameters=(1, 0.1, 0.1, 0.03), load_balancing=0,
                 min_max_clique_utilization_scheme=1,
                 sw_resource_balancing=0, sw_init=20000):
        ResourceAllocationILP.__init__(self, graph_model, obj_fun_parameters=obj_fun_parameters, load_balancing=load_balancing,
                 min_max_clique_utilization_scheme=min_max_clique_utilization_scheme,
                 sw_resource_balancing=sw_resource_balancing, sw_init=sw_init)

        self.coefficient_reembedding = coefficient_reembedding   # 10000 or 0
        self.dict_gees_G_value_old = dict()
        self.str_time_base = time.strftime("%Y%m%d%H%M%S") + str(int(int(datetime.utcnow().strftime('%f')) / 1000))

    def embed_and_then_reembed(self, old_requests, new_requests, time_limit=120, mip_gap=0.0001, flag_log=True):
        flag_ilp, first_success, second_success, res, resource_model = False, False, False, None, None
        first_success, _, __, delta_g_G_old = self.main_embed_old(old_requests, time_limit=time_limit, mip_gap=mip_gap, flag_log=flag_log)
        if first_success:
            second_success, res, resource_model, delta_g_G_new = self.main_reembed_new(new_requests, time_limit=time_limit, mip_gap=mip_gap, flag_log=flag_log)
        flag_ilp = second_success
        delta_g_G_reembedding = delta_g_G_new - delta_g_G_old
        delta_increase_dst_nodes = 1
        return flag_ilp, first_success, second_success, res, resource_model, delta_increase_dst_nodes, delta_g_G_reembedding

    def main_embed_old(self, old_requests, time_limit=120, mip_gap=0.0001, flag_log=True):
        self.str_time = self.str_time_base + '_old'
        self.flag_log = flag_log
        self.prepare_variables(old_requests)
        self.set_optimization_objective()
        self.declare_variables_flow()
        self.declare_variables_gee()
        self.add_constr_flow_conservation(old_requests)
        self.add_constr_flow_per_dst_vs_flow_by_request(old_requests)
        self.add_constr_gee_per_dst_vs_gee_by_request(old_requests)
        self.add_constr_flow_cliques(old_requests)
        self.add_constr_relation_between_flow_and_gee(old_requests)
        self.add_constr_path_split(old_requests)
        self.add_constr_gee_vs_loo(old_requests)
        self.add_constr_loo_limit(old_requests)
        self.add_constr_moo_limit(old_requests)
        self.add_constr_gee_exit_vs_moo(old_requests)
        if self.min_max_clique_utilization_scheme >= 1:
            self.add_constr_clique_utilization_max(old_requests)
        if self.min_max_clique_utilization_scheme >= 2:
            self.add_constr_clique_utilization_min(old_requests)
        if self.sw_resource_balancing > 0:
            self.add_constr_switch_utilization_max(old_requests)
            self.add_constr_switch_utilization_min(old_requests)

        self.c.parameters.timelimit.set(time_limit + 2)
        self.c.parameters.mip.tolerances.mipgap.set(mip_gap)
        start_time = time.time()
        if flag_log:
            self.c.write(self.str_time + "_generated.lp", "lp")
        if flag_log:
            self.fo = open(self.str_time + "_res.txt", 'a')
        try:
            self.c.solve()
        except CplexSolverError:
            print("Exception raised during solve")
            self.write("Exception raised during solve" + "\n")
            return False, None, None
        status = self.c.solution.get_status()
        print(self.c.solution.status[status])
        if status == self.c.solution.status.unbounded:
            self.write("Model is unbounded" + "\n")
            if self.flag_log:
                self.fo.close()
            print("Model is unbounded")
            return False, None, None
        if status == self.c.solution.status.infeasible:
            self.write("Model is infeasible" + "\n")
            if self.flag_log:
                self.fo.close()
            print("Model is infeasible")
            return False, None, None
        if status == self.c.solution.status.infeasible_or_unbounded:
            self.write("Model is infeasible or unbounded" + "\n")
            if flag_log:
                self.fo.close()
            print("Model is infeasible or unbounded")
            return False, None, None
        objective_value = self.c.solution.get_objective_value()
        print(objective_value)
        elasped_time = time.time() - start_time

        res = []
        all_flows_F = sorted(list(self.var_flow.set_all_flows_F))
        all_gees_G = sorted(list(self.var_gee.set_all_gees_G))
        all_loos = sorted(self.var_loo.list_all_loos)
        all_moos = sorted(self.var_moo.list_all_moos)

        print('All_gees_G = ', all_gees_G)

        self.write("Elapsed_time = " + str(elasped_time) + "\n")
        self.write("Solution value  = " + str(self.c.solution.get_objective_value()) + "\n")
        for i in range(len(all_flows_F)):
            flow_F = self.c.solution.get_values(all_flows_F[i])
            res.append(flow_F)
            self.write(all_flows_F[i] + "  " + str(flow_F) + "\n")
        self.write("\n")
        for i in range(len(all_gees_G)):
            gee_G = self.c.solution.get_values(all_gees_G[i])
            self.write(all_gees_G[i] + "  " + str(gee_G) + "\n")
        self.write("\n")
        for i in range(len(all_loos)):
            loo = self.c.solution.get_values(all_loos[i])
            self.write(all_loos[i] + "  " + str(loo) + "\n")
        self.write("\n")
        for i in range(len(all_moos)):
            moo = self.c.solution.get_values(all_moos[i])
            self.write(all_moos[i] + "  " + str(moo) + "\n")
        self.write("\n")

        for request in old_requests:
            request_id = request.request_id
            for i in range(1, self.number_links_transmission + 1):
                gees_G = self.var_gee.dict_gee_G_by_request[request_id].dict_gees_G[i][:]
                gee_G_a, gee_G_b = gees_G[0], gees_G[1]
                value_gee_G_a = int(float(self.c.solution.get_values(gee_G_a)))
                value_gee_G_b = int(float(self.c.solution.get_values(gee_G_b)))
                self.dict_gees_G_value_old[gee_G_a] = value_gee_G_a
                self.dict_gees_G_value_old[gee_G_b] = value_gee_G_b

        assert len(self.dict_gees_G_value_old) == len(all_gees_G)

        if self.flag_log:
            self.fo.close()
        return True, -99999, None, 1

    def main_reembed_new(self, new_requests, time_limit=120, mip_gap=0.0001, flag_log=True):
        self.c = cplex.Cplex()  # Reinitialize the Cplex environment
        self.var_flow = VariableFlow()
        self.var_gee = VarialbeGee()
        self.var_loo = VariableLoo()
        self.var_moo = VariableMoo()
        self.var_misc = VariableMisc()

        self.str_time = self.str_time_base + '_new'
        self.flag_log = flag_log
        self.prepare_variables(new_requests)

        '''
        Here is what is changed.
        '''
        # self.set_optimization_objective()
        self.set_optimization_objective_reembedding()
        # self.declare_variables_gee()
        self.declare_variables_gee_without_G()

        self.declare_variables_flow()

        self.add_constr_flow_conservation(new_requests)
        self.add_constr_flow_per_dst_vs_flow_by_request(new_requests)
        self.add_constr_gee_per_dst_vs_gee_by_request(new_requests)
        self.add_constr_flow_cliques(new_requests)
        self.add_constr_relation_between_flow_and_gee(new_requests)
        self.add_constr_path_split(new_requests)
        self.add_constr_gee_vs_loo(new_requests)
        self.add_constr_loo_limit(new_requests)
        self.add_constr_moo_limit(new_requests)
        self.add_constr_gee_exit_vs_moo(new_requests)
        if self.min_max_clique_utilization_scheme >= 1:
            self.add_constr_clique_utilization_max(new_requests)
        if self.min_max_clique_utilization_scheme >= 2:
            self.add_constr_clique_utilization_min(new_requests)
        if self.sw_resource_balancing > 0:
            self.add_constr_switch_utilization_max(new_requests)
            self.add_constr_switch_utilization_min(new_requests)

        self.c.parameters.timelimit.set(time_limit + 2)
        self.c.parameters.mip.tolerances.mipgap.set(mip_gap)
        start_time = time.time()
        if flag_log:
            self.c.write(self.str_time + "_generated.lp", "lp")
        if flag_log:
            self.fo = open(self.str_time + "_res.txt", 'a')
        try:
            self.c.solve()
        except CplexSolverError:
            print("Exception raised during solve")
            self.write("Exception raised during solve" + "\n")
            return False, None, None
        status = self.c.solution.get_status()
        print(self.c.solution.status[status])
        if status == self.c.solution.status.unbounded:
            self.write("Model is unbounded" + "\n")
            if self.flag_log:
                self.fo.close()
            print("Model is unbounded")
            return False, None, None
        if status == self.c.solution.status.infeasible:
            self.write("Model is infeasible" + "\n")
            if self.flag_log:
                self.fo.close()
            print("Model is infeasible")
            return False, None, None
        if status == self.c.solution.status.infeasible_or_unbounded:
            self.write("Model is infeasible or unbounded" + "\n")
            if flag_log:
                self.fo.close()
            print("Model is infeasible or unbounded")
            return False, None, None
        objective_value = self.c.solution.get_objective_value()
        print(objective_value)
        elasped_time = time.time() - start_time

        res = []
        all_flows_F = sorted(list(self.var_flow.set_all_flows_F))
        all_gees_G = sorted(list(self.var_gee.set_all_gees_G))
        all_loos = sorted(self.var_loo.list_all_loos)
        all_moos = sorted(self.var_moo.list_all_moos)

        self.write("Elapsed_time = " + str(elasped_time) + "\n")
        self.write("Solution value  = " + str(self.c.solution.get_objective_value()) + "\n")
        for i in range(len(all_flows_F)):
            flow_F = self.c.solution.get_values(all_flows_F[i])
            res.append(flow_F)
            self.write(all_flows_F[i] + "  " + str(flow_F) + "\n")
        self.write("\n")
        for i in range(len(all_gees_G)):
            gee_G = self.c.solution.get_values(all_gees_G[i])
            self.write(all_gees_G[i] + "  " + str(gee_G) + "\n")
        self.write("\n")
        for i in range(len(all_loos)):
            loo = self.c.solution.get_values(all_loos[i])
            self.write(all_loos[i] + "  " + str(loo) + "\n")
        self.write("\n")
        for i in range(len(all_moos)):
            moo = self.c.solution.get_values(all_moos[i])
            self.write(all_moos[i] + "  " + str(moo) + "\n")
        self.write("\n")

        resource_consume = ResourceModel(number_nodes=self.number_nodes, number_links_transmission=self.number_links_transmission)
        for request in new_requests:
            list_dst = request.list_dst
            request_id = request.request_id
            for i in list_dst:
                resource_consume.dict_node_id_openflow_table_decrease[i] += 1
            for i in range(1, self.number_nodes + 1):
                loo = self.var_loo.dict_loo_by_request[request_id].dict_loos[i]
                resource_consume.dict_node_id_openflow_table_decrease[i] += int(float(self.c.solution.get_values(loo)))
                moo = self.var_moo.dict_moo_by_request[request_id].dict_moos[i]
                resource_consume.dict_node_id_group_table_decrease[i] += int(float(self.c.solution.get_values(moo)))

        flows_F = sorted(list(self.var_flow.set_all_flows_F))
        for _f in flows_F:
            bw = int(float(self.c.solution.get_values(_f)))
            resource_consume.total_bw_consumed += bw
            resource_consume.dict_link_id_total_bw_consumption[self.var_flow.dict_flow_link_id[_f]] += bw
            resource_consume.total_interference_brought += bw * \
                self.dict_interference_pair_info[self.var_flow.dict_flow_link_id[_f]].num_of_interference_pairs

        # here objective_value should include the OF switch resource of list_dst ?
        # No, it's not necessary to do that.
        objective_value += self.obj_fun_parameters[1] * sum([len(request.list_dst) for request in new_requests])

        self.write(str(resource_consume))
        if self.flag_log:
            self.fo.close()
        return True, objective_value, resource_consume, 1

    def set_optimization_objective_reembedding(self):
        self.c.objective.set_sense(self.c.objective.sense.minimize)
        flows_F = sorted(list(self.var_flow.set_all_flows_F))
        obj_func = [self.obj_fun_parameters[0] +
                    self.obj_fun_parameters[3] * self.dict_interference_pair_info[
                        self.var_flow.dict_flow_link_id[_f]].num_of_interference_pairs for _f in flows_F]
        ctype = ''.join([self.var_flow.var_type for _ in range(len(flows_F))])
        loos = self.var_loo.list_all_loos[:]
        moos = self.var_moo.list_all_moos[:]
        '''
        Should be: gamma * (clique_utilization_max - average_clique_utilization_previous).
        However, this gives the same results. Nothing changes in fact: it's an objective
        function, not a constraint !
        '''
        list_clique_utilization = []
        if self.min_max_clique_utilization_scheme >= 1:
            list_clique_utilization.append(self.var_misc.clique_utilization_max)
        if self.min_max_clique_utilization_scheme >= 2:
            list_clique_utilization.append(self.var_misc.clique_utilization_min)
        list_switch_utilization = []
        if self.sw_resource_balancing > 0:
            list_switch_utilization.append(self.var_misc.switch_utilization_max)
            list_switch_utilization.append(self.var_misc.switch_utilization_min)
        obj_func += [self.obj_fun_parameters[1] for _ in range(len(loos))]
        obj_func += [self.obj_fun_parameters[2] for _ in range(len(moos))]
        if self.min_max_clique_utilization_scheme >= 1:
            obj_func.append(self.load_balancing)
        if self.min_max_clique_utilization_scheme >= 2:
            obj_func.append(-1 * self.load_balancing)
        if self.sw_resource_balancing > 0:
            obj_func.append(self.sw_resource_balancing)
            obj_func.append(-1 * self.sw_resource_balancing)
        ctype += ''.join([self.var_loo.var_type for _ in range(len(loos))])
        ctype += ''.join([self.var_moo.var_type for _ in range(len(moos))])
        if self.min_max_clique_utilization_scheme >= 1:
            ctype += 'I'
        if self.min_max_clique_utilization_scheme >= 2:
            ctype += 'I'
        if self.sw_resource_balancing > 0:
            ctype += 'II'

        '''
        --> -1 * coefficient_reembedding * \sum{g_var \in all_gees_G}{ g_o * g }
        --> The other term is just a constant, there is no need to take that into consideration.        
        '''
        all_gees_G = sorted(list(self.var_gee.set_all_gees_G))
        for gee_G in all_gees_G:
            obj_func.append(-1 * self.coefficient_reembedding * self.dict_gees_G_value_old[gee_G])
            ctype += 'B'
        self.c.variables.add(obj=obj_func, types=ctype,
                             names=(flows_F + loos + moos + list_clique_utilization
                                    + list_switch_utilization + all_gees_G))

    def declare_variables_gee_without_G(self):
        gees = self.var_gee.list_all_gees[:]
        ctype = ''.join([self.var_gee.var_type for _ in range(len(gees))])
        self.c.variables.add(types=ctype, names=gees)



