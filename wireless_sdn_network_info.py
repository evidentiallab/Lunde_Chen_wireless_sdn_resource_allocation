class ChannelInfo(object):
    def __init__(self, ch):
        self.ch        = ch
        self.nodes_set = set()
        self.links_set = set()
        self.links_list = []
        self.tuples_set = set()

class SharedTransLinkChannelInfo(object):
    def __init__(self, ch):
        self.ch                      = ch
        self.set_src                 = set()
        self.dict_src_link_tuple         = {}
        self.dict_link_tuple_link_tuple  = {}
        self.list_shared_link_tuples     = []
        self.number_of_shared_links      = 0

class MultiLinkInfo(object):
    def __init__(self, src, dst): # We should always force src < dst in a link representation
        self.src, self.dst   = src, dst
        self.channels_set    = set()
        self.links_set       = set()
        self.channel_link_dict = {}
        self.link_channel_dict = {}
        self.is_multi_link     = False

class BandwidthInfo(object):
    def __init__(self, index):
        self.index     = index
        self.bw_residu = 0
        self.capacity  = 0

    def get_attributes_from_link(self, link):
        self.index     = link.index
        self.capacity  = link.capacity
        self.bw_residu = link.bw_residu

    def consume_bandwidth(self, bw_consume):
        self.bw_residu -= bw_consume

class OpenFlowTablesInfo(object):
    def __init__(self, index):
        self.index = index
        self.openflow_entries_residu = None
        self.group_entries_residu    = None

    def get_attributes_from_node(self, node):
        self.index     = node.index
        self.openflow_entries_residu  = node.openflow_entries_residu
        self.group_entries_residu = node.group_entries_residu

class InterferencePairInfo(object):
    def __init__(self, link_id):
        self.set_interference_links = set()
        self.num_of_interference_pairs = 0

class Node(object):
    def __init__(self):
        self.index = None
        self.xy    = None
        self.openflow_entries_residu = None
        self.group_entries_residu    = None
        self.links_transmission = {}
        self.links_interference = {}
        self.links_illustration = {}
        self.channels = set()

class Link(object):
    def __init__(self):
        self.index = None
        self.src = None
        self.dst = None
        self.channel = None
        self.color   = None
        self.capacity = None
        self.bw_residu = None
        self.is_interference_link = False
        self.line_style = "solid"

class LinkTransmission(Link):
    def __init__(self):
        Link.__init__(self)

    def get_attributes_from_link(self, link):
        self.index = link.index
        self.src = link.src
        self.dst = link.dst
        self.channel = link.channel
        self.color = link.color
        self.capacity = link.capacity
        self.bw_residu = link.bw_residu
        self.is_interference_link = False
        self.line_style = "solid"

class LinkInterference(Link):
    def __init__(self):
        Link.__init__(self)

    def get_attributes_from_link(self, link):
        self.index = link.index
        self.src = link.src
        self.dst = link.dst
        self.channel = link.channel
        self.color = link.color
        self.capacity = 0
        self.bw_residu = 0
        self.is_interference_link = True
        self.line_style = "dashed"

class LinkIllustration(Link):
    def __init__(self):
        Link.__init__(self)

    def get_attributes_from_link(self, link):
        self.index = link.index
        self.src = link.src
        self.dst = link.dst
        self.channel = link.channel
        self.color = link.color
        self.is_interference_link = link.is_interference_link
        self.line_style = link.line_style

