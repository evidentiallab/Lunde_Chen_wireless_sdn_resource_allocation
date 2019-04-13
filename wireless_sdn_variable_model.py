class Flow(object):
    def __init__(self):
        pass


class FlowByNode(Flow):
    def __init__(self, node_id):
        Flow.__init__(self)
        self.node_id  = node_id
        self.flows_exit  = {}
        self.flows_enter = {}


class FlowByLink(Flow):
    def __init__(self, link_id):
        Flow.__init__(self)
        self.link_id     = link_id
        self.dict_flow_a = {}
        self.dict_flow_b = {}


class FlowByRequest(Flow):
    def __init__(self, request_id):
        Flow.__init__(self)
        self.request_id = request_id
        self.dict_flows_F = {}


class VariableFlow(object):
    '''
    "Flow" corresponds to the variable "F" in our paper.
    '''
    def __init__(self):
        self.var_type = "I"
        self.list_all_flows = []
        self.set_all_flows_F = set()
        self.dict_flow_by_node    = {}
        self.dict_flow_by_link    = {}
        self.dict_flow_F_by_request = {}
        self.dict_flow_link_id = {}


class Gee(object):
    def __init__(self):
        pass


class GeeByNode(Gee):
    def __init__(self, node_id):
        Gee.__init__(self)
        self.node_id  = node_id
        self.gees_exit  = {}
        self.gees_enter = {}


class GeeByLink(Gee):
    def __init__(self, link_id):
        Gee.__init__(self)
        self.link_id     = link_id
        self.dict_gee_a = {}
        self.dict_gee_b = {}


class GeeByRequest(Gee):
    def __init__(self, request_id):
        Gee.__init__(self)
        self.request_id = request_id
        self.dict_gees_G = {}
        self.gees_G_exit = {}


class VarialbeGee(object):
    '''
    "Gee" corresponds to the variable "G" in our paper.
    '''
    def __init__(self):
        self.var_type = "B"
        self.list_all_gees = []
        self.set_all_gees_G = set()
        self.dict_gee_by_node = {}
        self.dict_gee_by_link = {}
        self.dict_gee_G_by_request = {}


class LooByRequest(object):
    def __init__(self, request_id):
        self.request_id = request_id
        self.dict_loos = {}


class VariableLoo(object):
    '''
    "Loo" corresponds to the variable "L" in our paper.
    '''
    def __init__(self):
        self.var_type = "B"
        self.dict_loo_by_request = {}
        self.list_all_loos = []


class MooByRequest(object):
    def __init__(self, request_id):
        self.request_id = request_id
        self.dict_moos = {}


class VariableMoo(object):
    '''
    "Moo" corresponds to the variable "M" in our paper.
    '''
    def __init__(self):
        self.var_type = "B"
        self.dict_moo_by_request = {}
        self.list_all_moos = []


class VariableMisc(object):
    def __init__(self):
        self.clique_utilization_max = ''
        self.clique_utilization_min = ''
        self.switch_utilization_max = ''
        self.switch_utilization_min = ''
