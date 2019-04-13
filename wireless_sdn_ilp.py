from __future__ import print_function
import time
import cplex
from cplex.exceptions import CplexSolverError
from wireless_sdn_variable_model import *
import copy
from wireless_sdn_graph_model import ResourceModel


class ResourceAllocationILP(object):
    '''
    "Flow" corresponds to the variable "F" in our paper.
    "Gee" corresponds to the variable "G" in our paper.
    "Loo" corresponds to the variable "L" in our paper.
    "Moo" corresponds to the variable "M" in our paper.
    '''

    def __init__(self, graph_model, obj_fun_parameters=(1, 0.1, 0.1, 0.03), load_balancing=0,
                 min_max_clique_utilization_scheme=1,
                 sw_resource_balancing=0, sw_init=20000):
        self.graph_model = graph_model
        self.G = self.graph_model.G
        self.number_links_transmission = self.graph_model.number_links_transmission
        self.number_nodes = self.graph_model.number_nodes
        self.shared_trans_link_channel_info_dict = self.graph_model.shared_trans_link_channel_info_dict
        self.all_cliques = self.graph_model.all_cliques
        self.str_time = self.graph_model.str_time
        self.flag_log = True
        self.fo       = None
        self.c = cplex.Cplex()

        self.var_flow = VariableFlow()
        self.var_gee  = VarialbeGee()
        self.var_loo = VariableLoo()
        self.var_moo = VariableMoo()
        self.var_misc = VariableMisc()

        self.dict_link_clique_id = self.graph_model.dict_link_clique_id
        self.dict_clique_id_residual_capacity = self.graph_model.dict_clique_id_residual_capacity
        self.dict_clique_id_clique = self.graph_model.dict_clique_id_clique

        self.obj_fun_parameters = obj_fun_parameters
        self.load_balancing = load_balancing
        self.min_max_clique_utilization_scheme = min_max_clique_utilization_scheme
        self.sw_resource_balancing = sw_resource_balancing
        self.sw_init = sw_init

        '''
        Here we deepcopy network information in the objective to decouple the network model
        and the calculation, so that comparisons could be set up more easily.
        However, if we don't need to investigate how different parameters could impact our model,
        the deepcopy here makes little sense and could be a little bit confusing.
        '''
        self.bw_info_dict = copy.deepcopy(self.graph_model.bw_info_dict)
        self.of_table_info_dict = copy.deepcopy(self.graph_model.of_table_info_dict)
        self.dict_interference_pair_info = copy.deepcopy(self.graph_model.dict_interference_pair_info)

    def main(self, requests, time_limit=120, mip_gap=0.0001, flag_log=True):
        self.flag_log = flag_log
        self.prepare_variables(requests)
        self.set_optimization_objective()
        self.declare_variables_flow()
        self.declare_variables_gee()
        self.add_constr_flow_conservation(requests)
        self.add_constr_flow_per_dst_vs_flow_by_request(requests)
        self.add_constr_gee_per_dst_vs_gee_by_request(requests)
        self.add_constr_flow_cliques(requests)
        self.add_constr_relation_between_flow_and_gee(requests)
        self.add_constr_path_split(requests)
        self.add_constr_gee_vs_loo(requests)
        self.add_constr_loo_limit(requests)
        self.add_constr_moo_limit(requests)
        self.add_constr_gee_exit_vs_moo(requests)
        if self.min_max_clique_utilization_scheme >= 1:
            self.add_constr_clique_utilization_max(requests)
        if self.min_max_clique_utilization_scheme >= 2:
            self.add_constr_clique_utilization_min(requests)
        if self.sw_resource_balancing > 0:
            self.add_constr_switch_utilization_max(requests)
            self.add_constr_switch_utilization_min(requests)

        self.c.parameters.timelimit.set(time_limit + 2)
        # https://www.ibm.com/support/knowledgecenter/SSSA5P_12.5.0/ilog.odms.cplex.help/CPLEX/UsrMan/topics/discr_optim/mip/usage/11_terminate.html
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
        # if elasped_time >= time_limit:
        #     print("WARNING: elasped_time >= time_limit")
        #     print("objective_value = " + str(objective_value))
        #     return False, None, None

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
        for request in requests:
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
        objective_value += self.obj_fun_parameters[1] * sum([len(request.list_dst) for request in requests])

        self.write(str(resource_consume))
        if self.flag_log:
            self.fo.close()
        return True, objective_value, resource_consume

    def write(self, string):
        if self.flag_log:
            self.fo.write(string)

    def add_linear_constraint(self, vector_variable, vector_coeff, sense, rhs):
        self.c.linear_constraints.add(lin_expr=
            [cplex.SparsePair(ind=vector_variable, val=vector_coeff)], senses=sense, rhs=rhs)

    def set_optimization_objective_only_total_bandwidth(self):
        self.c.objective.set_sense(self.c.objective.sense.minimize)
        flows_F = sorted(list(self.var_flow.set_all_flows_F))
        obj_func = [1 for _ in flows_F]
        ctype = ''.join([self.var_flow.var_type for _ in range(len(flows_F))])
        self.c.variables.add(obj=obj_func, types=ctype, names=flows_F)

    def set_optimization_objective(self):
        '''
        --> Here we implement:
        \alpha \sum_{k\in k} \sum_{v \in V} \sum_{\lambda \in \channel{v}}   f_k(v, \lambda) 
        + \beta \sum_{k\in k} \sum_{v \in V} \sum_{\lambda \in \channel{v}} \norm{I(v, \lambda)}  f_k(v, \lambda)
        Because \norm{I(v, \lambda) is the size of the clique.
        '''
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
        self.c.variables.add(obj=obj_func, types=ctype,
                             names=(flows_F + loos + moos + list_clique_utilization + list_switch_utilization))

    def declare_variables_flow(self):
        '''
        "Flow" corresponds to the variable "F" in our paper.
        '''
        flows = self.var_flow.list_all_flows[:]
        ctype  = ''.join([self.var_flow.var_type for _ in range(len(flows))])
        self.c.variables.add(types=ctype, names=flows)

    def declare_variables_gee(self):
        '''
        # "Gee" corresponds to the variable "G" in our paper.
        '''
        gees = self.var_gee.list_all_gees[:]
        ctype = ''.join([self.var_gee.var_type for _ in range(len(gees))])
        self.c.variables.add(types=ctype, names=gees)

        gees_G = sorted(list(self.var_gee.set_all_gees_G))
        ctype = ''.join([self.var_gee.var_type for _ in range(len(gees_G))])
        self.c.variables.add(types=ctype, names=gees_G)

    def prepare_variables(self, requests): # Prepare variables
        self.var_misc.clique_utilization_max = 'maxCliqueUtilization'
        self.var_misc.clique_utilization_min = 'minCliqueUtilization'
        self.var_misc.switch_utilization_max = 'maxSwitchUtilization'
        self.var_misc.switch_utilization_min = 'minSwitchUtilization'
        for i in range(1, self.graph_model.number_nodes + 1):
            self.var_flow.dict_flow_by_node[i] = FlowByNode(i)
        for i in range(1, self.number_links_transmission + 1):
            self.var_flow.dict_flow_by_link[i] = FlowByLink(i)

        for i in range(1, self.graph_model.number_nodes + 1):
            self.var_gee.dict_gee_by_node[i] = GeeByNode(i)
        for i in range(1, self.number_links_transmission + 1):
            self.var_gee.dict_gee_by_link[i] = GeeByLink(i)

        for request in requests:
            request_id = request.request_id
            self.var_flow.dict_flow_F_by_request[request_id] = FlowByRequest(request_id)
            self.var_gee.dict_gee_G_by_request[request_id] = GeeByRequest(request_id)
            self.var_loo.dict_loo_by_request[request_id] = LooByRequest(request_id)
            self.var_moo.dict_moo_by_request[request_id] = MooByRequest(request_id)

        for request in requests:
            request_id = request.request_id
            src        = request.src
            list_dst   = request.list_dst

            for i in range(1, self.number_nodes + 1):
                loo = "L" + str(request_id) + "l" + str(i)
                self.var_loo.dict_loo_by_request[request_id].dict_loos[i] = loo
                self.var_loo.list_all_loos.append(loo)

                moo = "M" + str(request_id) + "m" + str(i)
                self.var_moo.dict_moo_by_request[request_id].dict_moos[i] = moo
                self.var_moo.list_all_moos.append(moo)

            dict_flows_F = self.var_flow.dict_flow_F_by_request[request_id].dict_flows_F
            dict_gees_G = self.var_gee.dict_gee_G_by_request[request_id].dict_gees_G
            gees_G_exit  = self.var_gee.dict_gee_G_by_request[request_id].gees_G_exit

            '''
            if transLink(i) shares a channel and a source node with another transLink(j),
            then they should be allocated the same flow_F variable.
            if transLink(i) shares a channel and a destination node with another transLink(j),
            then they should be allocated the same flow_F variable.
            '''
            for i in range(1, self.number_links_transmission + 1):
                link_t = self.graph_model.int_link_transmission_dict[i]
                ch = link_t.channel
                s, t = link_t.src, link_t.dst
                link_map_a = self.shared_trans_link_channel_info_dict[ch].dict_link_tuple_link_tuple[(s, t)]
                link_map_b = self.shared_trans_link_channel_info_dict[ch].dict_link_tuple_link_tuple[(t, s)]
                flow_F_a = "F" + str(request_id) + "s" + str(link_map_a[0]) + "t" + str(link_map_a[1]) + "c" + str(ch)
                flow_F_b = "F" + str(request_id) + "s" + str(link_map_b[0]) + "t" + str(link_map_b[1]) + "c" + str(ch)
                dict_flows_F[i] = [flow_F_a, flow_F_b]
                self.var_flow.set_all_flows_F.add(flow_F_a)
                self.var_flow.set_all_flows_F.add(flow_F_b)
                self.var_flow.dict_flow_link_id[flow_F_a] = i
                self.var_flow.dict_flow_link_id[flow_F_b] = i

                gee_G_a = "G" + str(request_id) + "s" + str(link_map_a[0]) + "t" + str(link_map_a[1]) + "c" + str(ch)
                gee_G_b = "G" + str(request_id) + "s" + str(link_map_b[0]) + "t" + str(link_map_b[1]) + "c" + str(ch)
                dict_gees_G[i] = [gee_G_a, gee_G_b]
                self.var_gee.set_all_gees_G.add(gee_G_a)
                self.var_gee.set_all_gees_G.add(gee_G_b)

                gees_G_exit_s = gees_G_exit.setdefault(s, [])
                if gee_G_a not in gees_G_exit_s:
                    gees_G_exit_s.append(gee_G_a)
                gees_G_exit_t = gees_G_exit.setdefault(t, [])
                if gee_G_b not in gees_G_exit_t:
                    gees_G_exit_t.append(gee_G_b)

            for dst in list_dst:
                '''
                Transmission links are numbered from 1 to 
                self.number_links_transmission
                '''
                flow_head = "f" + str(request_id) + "D" + str(dst)
                gee_head = "g" + str(request_id) + "D" + str(dst)
                for i in range(1, self.number_links_transmission + 1):
                    link_t = self.graph_model.int_link_transmission_dict[i]
                    ch = link_t.channel
                    flow_a = flow_head + "a" + str(i) # forward
                    flow_b = flow_head + "b" + str(i) # back
                    self.var_flow.list_all_flows += [flow_a, flow_b]
                    self.var_flow.dict_flow_by_node[link_t.src].flows_exit.setdefault(request_id,
                        {}).setdefault(dst, []).append(flow_a)
                    self.var_flow.dict_flow_by_node[link_t.src].flows_enter.setdefault(request_id,
                        {}).setdefault(dst, []).append(flow_b)
                    self.var_flow.dict_flow_by_node[link_t.dst].flows_exit.setdefault(request_id,
                        {}).setdefault(dst, []).append(flow_b)
                    self.var_flow.dict_flow_by_node[link_t.dst].flows_enter.setdefault(request_id,
                        {}).setdefault(dst, []).append(flow_a)
                    self.var_flow.dict_flow_by_link[i].dict_flow_a.setdefault(request_id,
                        []).append(flow_a)
                    self.var_flow.dict_flow_by_link[i].dict_flow_b.setdefault(request_id,
                        []).append(flow_b)

                    gee_a = gee_head + "a" + str(i)
                    gee_b = gee_head + "b" + str(i)
                    self.var_gee.list_all_gees += [gee_a, gee_b]
                    self.var_gee.dict_gee_by_node[link_t.src].gees_exit.setdefault(request_id,
                        {}).setdefault(dst, []).append(gee_a)
                    self.var_gee.dict_gee_by_node[link_t.src].gees_enter.setdefault(request_id,
                        {}).setdefault(dst, []).append(gee_b)
                    self.var_gee.dict_gee_by_node[link_t.dst].gees_exit.setdefault(request_id,
                        {}).setdefault(dst, []).append(gee_b)
                    self.var_gee.dict_gee_by_node[link_t.dst].gees_enter.setdefault(request_id,
                        {}).setdefault(dst, []).append(gee_a)
                    self.var_gee.dict_gee_by_link[i].dict_gee_a.setdefault(request_id,
                        []).append(gee_a)
                    self.var_gee.dict_gee_by_link[i].dict_gee_b.setdefault(request_id,
                        []).append(gee_b)

    def add_constr_clique_utilization_max(self, requests):
        '''
        For each clique c:
        zeta_prime(c) + \sum_{k \in K} \sum_{v \in S(c)} f(v, \lambda) <= Zeta_max
        '''
        for clique_id, clique in self.dict_clique_id_clique.items():
            vector_coeff = []
            vector_variable = []
            sense = ["L"]
            for link_id in clique:
                for request in requests:
                    request_id = request.request_id
                    flows_F = self.var_flow.dict_flow_F_by_request[request_id].dict_flows_F[link_id]
                    for f in flows_F:
                        if f not in vector_variable:
                            vector_variable.append(f)
                            vector_coeff.append(1)
                        else:
                            index = vector_variable.index(f)
                            vector_coeff[index] += 0
            vector_coeff.append(-1)
            vector_variable.append(self.var_misc.clique_utilization_max)
            clique_bw_residual = self.dict_clique_id_residual_capacity[clique_id]
            rhs = [clique_bw_residual - self.graph_model.json_channels[1]['capacity']]
            self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_clique_utilization_min(self, requests):
        '''
        For each clique c:
        -1 * zeta_prime(c) + (-1) * \sum_{k \in K} \sum_{v \in S(c)} f(v, \lambda) <= -1 * Zeta_min
        '''
        for clique_id, clique in self.dict_clique_id_clique.items():
            vector_coeff = []
            vector_variable = []
            sense = ["L"]
            for link_id in clique:
                for request in requests:
                    request_id = request.request_id
                    flows_F = self.var_flow.dict_flow_F_by_request[request_id].dict_flows_F[link_id]
                    for f in flows_F:
                        if f not in vector_variable:
                            vector_variable.append(f)
                            vector_coeff.append(-1)
                        else:
                            index = vector_variable.index(f)
                            vector_coeff[index] += 0
            vector_coeff.append(1)
            vector_variable.append(self.var_misc.clique_utilization_min)
            clique_bw_residual = self.dict_clique_id_residual_capacity[clique_id]
            rhs = [-1 * clique_bw_residual + self.graph_model.json_channels[1]['capacity']]
            self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_flow_cliques(self, requests):  # Equation 7
        for clique_id, clique in self.dict_clique_id_clique.items():
            vector_coeff = []
            vector_variable = []
            sense = ["L"]
            for link_id in clique:
                for request in requests:
                    request_id = request.request_id
                    flows_F = self.var_flow.dict_flow_F_by_request[request_id].dict_flows_F[link_id]
                    for f in flows_F:
                        if f not in vector_variable:
                            vector_variable.append(f)
                            vector_coeff.append(1)
                        else:
                            index = vector_variable.index(f)
                            '''
                            @IMPORTANT:
                            This coefficient should not increase by one when 
                            the corresponding variable is going to be shared 
                            among another link, because of the multicast advantage!
                            That's essentially one of the most important selling points
                            of our algorithm.
                            '''
                            vector_coeff[index] += 0
                            # vector_coeff[index] += 1
            # min_bw_residu = min([self.bw_info_dict[link_id].bw_residu for link_id in clique])
            clique_bw_residual = self.dict_clique_id_residual_capacity[clique_id]
            rhs = [clique_bw_residual]
            self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_flow_per_dst_vs_flow_by_request(self, requests): # Equation (6)
        for request in requests:
            request_id = request.request_id
            for i in range(1, self.number_links_transmission + 1):
                flows_F  = self.var_flow.dict_flow_F_by_request[request_id].dict_flows_F[i][:]
                flow_F_a, flow_F_b = flows_F[0], flows_F[1]
                for flow_a in self.var_flow.dict_flow_by_link[i].dict_flow_a[request_id]:
                    vector_coeff = [1, -1]
                    vector_variable = [flow_a, flow_F_a]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)
                for flow_b in self.var_flow.dict_flow_by_link[i].dict_flow_b[request_id]:
                    vector_coeff = [1, -1]
                    vector_variable = [flow_b, flow_F_b]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_gee_per_dst_vs_gee_by_request(self, requests):  # Equation (To-add-in-the-paper)
        for request in requests:
            request_id = request.request_id
            for i in range(1, self.number_links_transmission + 1):
                gees_G = self.var_gee.dict_gee_G_by_request[request_id].dict_gees_G[i][:]
                gee_G_a, gee_G_b = gees_G[0], gees_G[1]
                for gee_a in self.var_gee.dict_gee_by_link[i].dict_gee_a[request_id]:
                    vector_coeff = [1, -1]
                    vector_variable = [gee_a, gee_G_a]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)
                for gee_b in self.var_gee.dict_gee_by_link[i].dict_gee_b[request_id]:
                    vector_coeff = [1, -1]
                    vector_variable = [gee_b, gee_G_b]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_gee_exit_vs_moo(self, requests):  # Equation (3)
        '''
        This constraint:
                if sum_{g_exit(v)} >= 2, them m = 1
                else:  m = 0
        linearization method:
        2*m <= sum_g <= 1 + abs|number_of_channels|*m   
        '''

        for request in requests:
            request_id = request.request_id
            for i in range(1, self.number_nodes + 1):
                moo = self.var_moo.dict_moo_by_request[request_id].dict_moos[i]
                gees_G_exit = self.var_gee.dict_gee_G_by_request[request_id].gees_G_exit[i][:]

                vector_variable = [moo]
                vector_coeff = [2]
                sense = ["L"]
                rhs = [0]
                for gee_G in gees_G_exit:
                    vector_variable.append(gee_G)
                    vector_coeff.append(-1)
                self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

                vector_variable = [moo]
                vector_coeff = [-10000]
                sense = ["L"]
                rhs = [1]
                for gee_G in gees_G_exit:
                    vector_variable.append(gee_G)
                    vector_coeff.append(1)
                self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_moo_limit(self, requests): # equation (5)
        for i in range(1, self.number_nodes + 1):
            vector_variable = []
            vector_coeff = []
            sense = ["L"]
            rhs = [self.of_table_info_dict[i].group_entries_residu]
            for request in requests:
                request_id = request.request_id
                moo = self.var_moo.dict_moo_by_request[request_id].dict_moos[i]
                vector_variable.append(moo)
                vector_coeff.append(1)
            self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_loo_limit(self, requests): # equation (4)
        for i in range(1, self.number_nodes + 1):
            vector_variable = []
            vector_coeff = []
            sense = ["L"]
            rhs = [self.of_table_info_dict[i].openflow_entries_residu]
            for request in requests:
                request_id = request.request_id
                loo = self.var_loo.dict_loo_by_request[request_id].dict_loos[i]
                vector_variable.append(loo)
                vector_coeff.append(1)
            self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_switch_utilization_max(self, requests):
        '''
        For each node v:
        l_prime(v) + \sum_{k \in K} \sum_{v \in NodesAll} l(v) <= l_max
        '''
        for i in range(1, self.number_nodes + 1):
            vector_variable = []
            vector_coeff = []
            sense = ["L"]
            for request in requests:
                request_id = request.request_id
                loo = self.var_loo.dict_loo_by_request[request_id].dict_loos[i]
                vector_variable.append(loo)
                vector_coeff.append(1)
            vector_variable.append(self.var_misc.switch_utilization_max)
            vector_coeff.append(-1)
            rhs = [self.of_table_info_dict[i].openflow_entries_residu - self.sw_init]
            self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_switch_utilization_min(self, requests):
        '''
        For each node v:
        l_prime(v) + \sum_{k \in K} \sum_{v \in NodesAll} l(v) >= l_min
        '''
        for i in range(1, self.number_nodes + 1):
            vector_variable = []
            vector_coeff = []
            sense = ["G"]
            for request in requests:
                request_id = request.request_id
                loo = self.var_loo.dict_loo_by_request[request_id].dict_loos[i]
                vector_variable.append(loo)
                vector_coeff.append(1)
            vector_variable.append(self.var_misc.switch_utilization_min)
            vector_coeff.append(-1)
            rhs = [self.of_table_info_dict[i].openflow_entries_residu - self.sw_init]
            self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_gee_vs_loo(self, requests): #Equation (1) and (2)
        '''
        Attention: Here the implementation is different from what is written in the paper.
        In fact, the implementation becomes here:
        
        gee_G(v, lambda) <= l_k(v)
        l_k(v) <= sum(gee_G(v, lambda))
        
        After the ILP, ONE OpenFlow switch resource should be taken out from destination nodes, as here in this
        implementation it is node taken into consideration. This complicates quite a lot the writing,
        therefore we choose to not mention this complication. However, as this simplifies the ILP programming
        as well as reduces quite a lot the number of constraints, in our implementation we choose
        to adopt this way of modelling.
        '''
        for request in requests:
            request_id = request.request_id
            for i in range(1, self.number_nodes + 1):
                loo = self.var_loo.dict_loo_by_request[request_id].dict_loos[i]
                gees_G_exit = self.var_gee.dict_gee_G_by_request[request_id].gees_G_exit[i][:]
                '''
                Equation (1)
                '''
                for gee_G in gees_G_exit:
                    vector_variable = [gee_G, loo]
                    vector_coeff = [1, -1]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)
                '''
                Equation (2)
                '''
                vector_variable = [loo]
                vector_coeff = [1]
                sense = ["L"]
                rhs = [0]
                for gee_G in gees_G_exit:
                    vector_variable.append(gee_G)
                    vector_coeff.append(-1)
                self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_flow_conservation(self, requests): # Equation (8)
        for request in requests:
            request_id = request.request_id
            src = request.src
            list_dst = request.list_dst
            request_bw = request.request_bw
            for i in range(1, self.number_nodes + 1):
                for dst in list_dst:
                    flow_exit = self.var_flow.dict_flow_by_node[i].flows_exit[request_id][dst]
                    flow_enter = self.var_flow.dict_flow_by_node[i].flows_enter[request_id][dst]
                    flow_balance = 0
                    if i == src:
                        flow_balance = - request_bw
                    elif i == dst:
                        flow_balance = request_bw
                    vector_coeff = []
                    vector_variable = []
                    sense = ["E"]
                    for flow in flow_enter:
                        vector_coeff.append(1)
                        vector_variable.append(flow)
                    for flow in flow_exit:
                        vector_coeff.append(-1)
                        vector_variable.append(flow)
                    rhs = [flow_balance]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_relation_between_flow_and_gee(self, requests): # Equation (9)
        '''
        Again, here we use rather gee_G(v, lambda) rather than gee((v, u), lambda)
        '''
        for request in requests:
            request_id = request.request_id
            request_bw = request.request_bw
            traversed = []
            for i in range(1, self.number_links_transmission + 1):
                flows_F = self.var_flow.dict_flow_F_by_request[request_id].dict_flows_F[i][:]
                gees_G = self.var_gee.dict_gee_G_by_request[request_id].dict_gees_G[i][:]
                flow_F_a, flow_F_b = flows_F[0], flows_F[1]
                gee_G_a, gee_G_b = gees_G[0], gees_G[1]
                if (gee_G_a, flow_F_a) not in traversed:
                    traversed.append((gee_G_a, flow_F_a))
                    '''
                    left part of equation 
                    '''
                    vector_variable = [gee_G_a, flow_F_a]
                    vector_coeff = [1, -1]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)
                    '''
                    right part of equation 
                    '''
                    vector_variable = [flow_F_a, gee_G_a]
                    vector_coeff = [1, -1 * request_bw]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)
                if (gee_G_b, flow_F_b) not in traversed:
                    traversed.append((gee_G_b, flow_F_b))
                    '''
                    left part of equation 
                    '''
                    vector_variable = [gee_G_b, flow_F_b]
                    vector_coeff = [1, -1]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)
                    '''
                    right part of equation 
                    '''
                    vector_variable = [flow_F_b, gee_G_b]
                    vector_coeff = [1, -1 * request_bw]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

    def add_constr_path_split(self, requests): # Equation (10)
        for request in requests:
            request_id = request.request_id
            request_bw = request.request_bw
            path_split_ratio = request.path_split_ratio
            request_bw_min = int(path_split_ratio * request_bw)
            for i in range(1, self.number_links_transmission + 1):
                size = len(self.var_gee.dict_gee_by_link[i].dict_gee_a[request_id])
                if size != len(request.list_dst):
                    print("add_constr_path_split error, size != len(request.list_dst).")
                for j in range(size):
                    '''
                    right part of equation 
                    '''
                    gee_a = self.var_gee.dict_gee_by_link[i].dict_gee_a[request_id][j]
                    flow_a = self.var_flow.dict_flow_by_link[i].dict_flow_a[request_id][j]
                    vector_coeff = [1, -1 * request_bw]
                    vector_variable = [flow_a, gee_a]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

                    gee_b = self.var_gee.dict_gee_by_link[i].dict_gee_b[request_id][j]
                    flow_b = self.var_flow.dict_flow_by_link[i].dict_flow_b[request_id][j]
                    vector_coeff = [1, -1 * request_bw]
                    vector_variable = [flow_b, gee_b]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

                    '''
                    left part of equation 
                    '''
                    gee_a = self.var_gee.dict_gee_by_link[i].dict_gee_a[request_id][j]
                    flow_a = self.var_flow.dict_flow_by_link[i].dict_flow_a[request_id][j]
                    vector_coeff = [-1, request_bw_min]
                    vector_variable = [flow_a, gee_a]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)

                    gee_b = self.var_gee.dict_gee_by_link[i].dict_gee_b[request_id][j]
                    flow_b = self.var_flow.dict_flow_by_link[i].dict_flow_b[request_id][j]
                    vector_coeff = [-1, request_bw_min]
                    vector_variable = [flow_b, gee_b]
                    sense = ["L"]
                    rhs = [0]
                    self.add_linear_constraint(vector_variable, vector_coeff, sense, rhs)


class ResourceAllocationNoMulticastAdvantageILP(ResourceAllocationILP):
    '''
    The only modification to do: map f_1 and f_2 to F_1 and F_2 instead of to F_1 only.
    '''
    def prepare_variables(self, requests): # Prepare variables
        self.var_misc.clique_utilization_max = 'maxCliqueUtilization'
        self.var_misc.clique_utilization_min = 'minCliqueUtilization'
        self.var_misc.switch_utilization_max = 'maxSwitchUtilization'
        self.var_misc.switch_utilization_min = 'minSwitchUtilization'
        for i in range(1, self.graph_model.number_nodes + 1):
            self.var_flow.dict_flow_by_node[i] = FlowByNode(i)
        for i in range(1, self.number_links_transmission + 1):
            self.var_flow.dict_flow_by_link[i] = FlowByLink(i)

        for i in range(1, self.graph_model.number_nodes + 1):
            self.var_gee.dict_gee_by_node[i] = GeeByNode(i)
        for i in range(1, self.number_links_transmission + 1):
            self.var_gee.dict_gee_by_link[i] = GeeByLink(i)

        for request in requests:
            request_id = request.request_id
            self.var_flow.dict_flow_F_by_request[request_id] = FlowByRequest(request_id)
            self.var_gee.dict_gee_G_by_request[request_id] = GeeByRequest(request_id)
            self.var_loo.dict_loo_by_request[request_id] = LooByRequest(request_id)
            self.var_moo.dict_moo_by_request[request_id] = MooByRequest(request_id)

        for request in requests:
            request_id = request.request_id
            src        = request.src
            list_dst   = request.list_dst

            for i in range(1, self.number_nodes + 1):
                loo = "L" + str(request_id) + "l" + str(i)
                self.var_loo.dict_loo_by_request[request_id].dict_loos[i] = loo
                self.var_loo.list_all_loos.append(loo)

                moo = "M" + str(request_id) + "m" + str(i)
                self.var_moo.dict_moo_by_request[request_id].dict_moos[i] = moo
                self.var_moo.list_all_moos.append(moo)

            dict_flows_F = self.var_flow.dict_flow_F_by_request[request_id].dict_flows_F
            dict_gees_G = self.var_gee.dict_gee_G_by_request[request_id].dict_gees_G
            gees_G_exit  = self.var_gee.dict_gee_G_by_request[request_id].gees_G_exit

            '''
            if transLink(i) shares a channel and a source node with another transLink(j),
            then they should be allocated the same flow_F variable.
            if transLink(i) shares a channel and a destination node with another transLink(j),
            then they should be allocated the same flow_F variable.
            '''
            for i in range(1, self.number_links_transmission + 1):
                link_t = self.graph_model.int_link_transmission_dict[i]
                ch = link_t.channel
                s, t = link_t.src, link_t.dst
                flow_F_a = "F" + str(request_id) + "s" + str(s) + "t" + str(t) + "c" + str(ch)
                flow_F_b = "F" + str(request_id) + "s" + str(t) + "t" + str(s) + "c" + str(ch)
                dict_flows_F[i] = [flow_F_a, flow_F_b]
                self.var_flow.set_all_flows_F.add(flow_F_a)
                self.var_flow.set_all_flows_F.add(flow_F_b)
                self.var_flow.dict_flow_link_id[flow_F_a] = i
                self.var_flow.dict_flow_link_id[flow_F_b] = i

                gee_G_a = "G" + str(request_id) + "s" + str(s) + "t" + str(t) + "c" + str(ch)
                gee_G_b = "G" + str(request_id) + "s" + str(t) + "t" + str(s) + "c" + str(ch)
                dict_gees_G[i] = [gee_G_a, gee_G_b]
                self.var_gee.set_all_gees_G.add(gee_G_a)
                self.var_gee.set_all_gees_G.add(gee_G_b)

                gees_G_exit_s = gees_G_exit.setdefault(s, [])
                if gee_G_a not in gees_G_exit_s:
                    gees_G_exit_s.append(gee_G_a)
                gees_G_exit_t = gees_G_exit.setdefault(t, [])
                if gee_G_b not in gees_G_exit_t:
                    gees_G_exit_t.append(gee_G_b)

            for dst in list_dst:
                '''
                Transmission links are numbered from 1 to 
                self.number_links_transmission
                '''
                flow_head = "f" + str(request_id) + "D" + str(dst)
                gee_head = "g" + str(request_id) + "D" + str(dst)
                for i in range(1, self.number_links_transmission + 1):
                    link_t = self.graph_model.int_link_transmission_dict[i]
                    ch = link_t.channel
                    flow_a = flow_head + "a" + str(i) # forward
                    flow_b = flow_head + "b" + str(i) # back
                    self.var_flow.list_all_flows += [flow_a, flow_b]
                    self.var_flow.dict_flow_by_node[link_t.src].flows_exit.setdefault(request_id,
                        {}).setdefault(dst, []).append(flow_a)
                    self.var_flow.dict_flow_by_node[link_t.src].flows_enter.setdefault(request_id,
                        {}).setdefault(dst, []).append(flow_b)
                    self.var_flow.dict_flow_by_node[link_t.dst].flows_exit.setdefault(request_id,
                        {}).setdefault(dst, []).append(flow_b)
                    self.var_flow.dict_flow_by_node[link_t.dst].flows_enter.setdefault(request_id,
                        {}).setdefault(dst, []).append(flow_a)
                    self.var_flow.dict_flow_by_link[i].dict_flow_a.setdefault(request_id,
                        []).append(flow_a)
                    self.var_flow.dict_flow_by_link[i].dict_flow_b.setdefault(request_id,
                        []).append(flow_b)

                    gee_a = gee_head + "a" + str(i)
                    gee_b = gee_head + "b" + str(i)
                    self.var_gee.list_all_gees += [gee_a, gee_b]
                    self.var_gee.dict_gee_by_node[link_t.src].gees_exit.setdefault(request_id,
                        {}).setdefault(dst, []).append(gee_a)
                    self.var_gee.dict_gee_by_node[link_t.src].gees_enter.setdefault(request_id,
                        {}).setdefault(dst, []).append(gee_b)
                    self.var_gee.dict_gee_by_node[link_t.dst].gees_exit.setdefault(request_id,
                        {}).setdefault(dst, []).append(gee_b)
                    self.var_gee.dict_gee_by_node[link_t.dst].gees_enter.setdefault(request_id,
                        {}).setdefault(dst, []).append(gee_a)
                    self.var_gee.dict_gee_by_link[i].dict_gee_a.setdefault(request_id,
                        []).append(gee_a)
                    self.var_gee.dict_gee_by_link[i].dict_gee_b.setdefault(request_id,
                        []).append(gee_b)



