# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Class for storing and building potentical routing trees
'''
import logging
import math
from .utils import average_degree, distance


class RoutingTree(object):
    '''
    Represents a potential routing tree traced back from start node
    '''
    _root = None
    _levels = {}
    _nx_graph = None
    estimated_work = None

    def build(self, nx_graph, start_node_id, previous_node_id, max_hop, work_check=True):
        '''
        Build the routing tree
        :param nx_graph: networkx graph
        :param start_node_id: The first node the routing paths start from
        :param previous_node_id: The previous node is always known, so record it
        :param max_hop: How many hops to buld the routing table to
        :return: True if the tree was calculate; otherwise False
        '''
        self._nx_graph = nx_graph
        self._root = RoutingTree._Entry(start_node_id, 0)
        self._levels = {}
        self._levels[0] = [self._root]
        previous_node = self._add_child(self._root, previous_node_id)

        # estimate work load
        self.estimated_work = self._estimate_nodes_in_tree(nx_graph, max_hop)
        logging.debug('%d : Estimated work load for anonymity set',
                      self.estimated_work)
        if work_check and self.estimated_work > nx_graph.number_of_nodes() * 2:
            logging.debug('Not calculating anonymity set too large')
            return False

        # add the rest of the tree
        for child_id in nx_graph.neighbors(previous_node_id):
            self._build_tree(nx_graph, child_id, max_hop,
                             previous_node, [start_node_id, previous_node_id])

        logging.debug('%d : Actual work anonymity set work', self.get_count())
        return True

    def get_data_at_level(self, level):
        '''
        Get all inserted data at a given level
        :param level: Zero based index, can be a positive or
            negative reference to the level
        :return: list of data at that level
        '''
        if abs(level) > self.get_height() - 1:
            raise Exception('Out of bound index')
        return [i.data for i in self._levels[abs(level)]]

    def get_height(self):
        '''
        Height of the tree
        :return: int count of the number of levels
        '''
        # tree has a secret extra level, we use for the ranking calculations
        return len(self._levels.keys()) - 1

    def get_count(self):
        '''
        Count the number of nodes in the tree
        :return: int count
        '''
        length = 0
        for i in range(0, self.get_height()):
            length = length + len(self._levels[i])
        return length

    def get_sender_set(self):
        '''
        Return the list of the sender set
        :return: Unique list of senders
        '''
        # its dumb, set is not json serializable so turn it back into a list
        return list(set(self.get_data_at_level(self.get_height() - 1)))

    def get_sender_set_rank(self, rank_function, target_location):
        '''
        Calculate the rank of the sender set
        :param rank_function: Function used to rank a nodes routing choices
        :param target_location: The target location of the node
        :return: dict of the sender set nodes by rank
        '''
        if self.get_height() < 2:
            return {}
        if self.get_height() == 2:
            return {1: [self._root.children[0].data]}
        # known its 100% for the level 1 node (previous), so we can skip

        def distro_function(rank): return rank
        ranks = self._assign_sender_rank(
            rank_function, distro_function, self._root.children[0],
            target_location, self.get_height() - 3, 1)
        rank_set = {}
        for node, rank in ranks:
            if rank not in rank_set:
                rank_set[rank] = []
            rank_set[rank].append(node)
        return rank_set

    def get_sender_set_distribution(self, rank_function, distro_function, target_location):
        '''
        Calculate the probability distribution for the sender set
        :param rank_function: Function used to rank a nodes routing choices
        :param distro_function: Function that takes the rank outout and returns the
                                probability of that rank happening
        :param target_location: The target location of the node
        :return: dict of the probability distriution, sum(values) == 1
        '''
        if self.get_height() < 2:
            return {}
        if self.get_height() == 2:
            return {self._root.children[0].data: 1}
        # known its 100% for the level 1 node (previous), so we can skip
        distro = self._assign_sender_rank(
            rank_function, distro_function, self._root.children[0],
            target_location, self.get_height() - 3, 1)
        # combine entries for the same nodes
        distro_set = {}
        total = 0.0
        for node, prob in distro:
            if node not in distro_set:
                distro_set[node] = 0
            distro_set[node] = distro_set[node] + prob
            total = total + prob
        # normalize the distributions (e.g. their sum == 1)
        for node, prob in distro_set.items():
            distro_set[node] = prob / total
        return distro_set

    def rank_greedy(self, node, target_location, nx_graph):
        '''
        Calculate the parent node routing rank when greedy routing used.
        :param node: node to caluclate the rank for
        :param target_location: the message target location
        :param nx_graph: The networkx graph assoicated with this routing tree
        :return: int rank of parent getting routed to
        '''
        peers = {}
        for child_id in nx_graph.neighbors(node.data):
            peers[child_id] = distance(
                nx_graph.node[child_id]['location'], target_location)

        ordered = sorted(peers.items(), key=lambda x: x[1])
        for i in range(0, len(ordered)):
            if ordered[i][0] == node.parent.data:
                return i + 1
        raise Exception('SOmething went very very wrong')

    def distro_rank_exponetial_backoff(self, rank):
        '''
        Meant to be used as parameter to get_sender_set_distribution.
        Probability of a single nodes routing choices.
        This uses an exponential back off. .5, .25, .125, etc
        :param rank: the routing choice rank of a node
        :return: float
        '''
        return 0.5 ** rank

    def _assign_sender_rank(self, rank_function, distro_function, node, target_location,
                            current_hop_count, prob):
        distro = []
        for child in node.children:
            child_prob = distro_function(rank_function(
                child, target_location, self._nx_graph))
            if current_hop_count == 0:
                distro.append((child.data, prob * child_prob))
            else:
                distro.extend(self._assign_sender_rank(rank_function, distro_function,
                                                       child, target_location,
                                                       current_hop_count - 1,
                                                       prob * child_prob))
        return distro

    def _get_count(self, node):
        count = 0
        for child in node.children:
            count = count + self._get_count(child)
        return len(node.children) + count

    def _estimate_nodes_in_tree(self, nx_graph, hop_count):
        a_degree = average_degree(nx_graph)
        a_degree = int(math.ceil(a_degree)) - 1
        return int((a_degree**hop_count - 1) / (a_degree - 1))

    def _build_tree(self, nx_graph, node_id, current_hop, parent_node, current_path):
        if current_hop <= 0:
            return
        # check if we already routed through this node
        if node_id in current_path:
            return
        new_path = current_path[:]
        new_path.append(node_id)

        new_node = self._add_child(parent_node, node_id)
        # add children node
        for child_id in nx_graph.neighbors(node_id):
            self._build_tree(nx_graph, child_id,
                             current_hop - 1, new_node, new_path)

    def _get_path(self, start_node):
        if start_node is None:
            return []
        path = self._get_path(start_node.parent)
        path.append(start_node.data)
        return path

    def _add_child(self, node, child):
        '''
        Add new data element to the tree
        :param node: parent node
        :param child: new object to be added
        :return: new node added to the tree
        '''
        level = node.level + 1
        new_entry = RoutingTree._Entry(child, level, node)
        node.children.append(new_entry)
        if level not in self._levels:
            self._levels[level] = []
        self._levels[level].append(new_entry)
        return new_entry

    class _Entry(object):
        '''
        Reprents a tree structure
        '''
        children = []
        data = None
        level = None
        parent = None

        def __init__(self, data, level, parent=None):
            self.data = data
            self.children = []
            self.level = level
            self.parent = parent
