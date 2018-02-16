# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Class for storing and building potentical routing trees
'''
import logging
import math
from lib.utils import average_degree, distance


class RoutingTree(object):
    '''
    Represents a potential routing tree traced back from start node
    '''

    def __init__(self, nx_graph, routing_algorithm, max_rank=2):
        """Constructor

        Arguments:
            nx_graph {Graph} -- Topology graph
            routing_algorithm {function} -- Routing algorithm used by protocol

        Keyword Arguments:
            max_rank {int} -- Maximum rank of nodes to calculate
            a path for from each node. Top nodes will be followed. (default: {2})
        """
        self._root = None
        self._levels = {}
        self._sender_set = set()
        self._cache_rank_calculations = {}

        self._nx_graph = nx_graph
        self._routing_algorithm = routing_algorithm
        self._max_rank = max_rank

    def build(self, adversary_node_id, previous_node_id, max_hop, target_address):
        """Build the sender set and routing paths

        Arguments:
            adversary_node_id {int} -- ID of the adversary node in the nx_graph
            previous_node_id {int} -- ID of the previous node in the nx_graph
            max_hop {int} -- Number of hops to calculate the sender set and routing 
            paths back to
            target_address {float} -- Address of the node the message is routing to
        """
        self._root = None
        self._levels = {}
        self._sender_set = set()
        self._cache_rank_calculations = {}

        # calculate the preferred routing paths
        self._root = RoutingTree._Entry(adversary_node_id, 0)
        self._levels[0] = [self._root]
        self._build_tree(previous_node_id, max_hop + 1,
                         self._root, [adversary_node_id], target_address, 1)

        # calculate the sender set
        self._sender_set.add(adversary_node_id)
        self._build_sender_set([previous_node_id], max_hop)
        self._sender_set.remove(adversary_node_id)

        # check for case when all the neighbors only have a single connection
        # to the adversary node
        if self.get_height() == 1:
            # add an empty level after
            self._levels[2] = []

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

    def get_sender_set(self):
        '''
        Return the list of the sender set
        :return: Unique list of senders
        '''
        # its dumb, set is not json serializable so turn it back into a list
        return list(self._sender_set)

    def get_sender_set_rank(self):
        '''
        Calculate the rank of the sender set
        :return: dict of the sender set nodes by rank
        '''
        if self.get_height() < 2:
            return {}
        if self.get_height() == 2:
            return {1: [self._root.children[0].data]}
        # known its 100% for the level 1 node (previous), so we can skip

        # use rank value instead of a distribution
        def dist_function(rank): return rank

        # assign distribution
        ranks = self._assign_sender_dist(
            dist_function, self._root.children[0], self.get_height() - 3, 1)
        rank_set = {}
        largest_rank = 0
        processed_set = set()

        for node, rank in ranks:
            if rank not in rank_set:
                rank_set[rank] = []
            rank_set[rank].append(node)

            if rank > largest_rank:
                largest_rank = rank
            processed_set.add(node)

        # add in remaining nodes from the sender set
        largest_rank += 1
        for node in self.get_sender_set():
            if node in processed_set:
                continue
            if largest_rank not in rank_set:
                rank_set[largest_rank] = []
            rank_set[largest_rank].append(node)

        return rank_set

    def get_sender_set_distribution(self, dist_function):
        '''
        Calculate the probability distribution for the sender set
        :param dist_function: Function that takes the rank outout and returns the
                                probability of that rank happening
        :return: dict of the probability distriution, sum(values) == 1
        '''
        if self.get_height() < 2:
            return {}
        if self.get_height() == 2:
            return {self._root.children[0].data: 1}
        # known its 100% for the level 1 node (previous), so we can skip

        distro = self._assign_sender_dist(
            dist_function, self._root.children[0], self.get_height() - 3, 1)

        # every node in the sender set and not in this distribution set has a probability of zero
        # Don't need to add these since they will not affect the final probability distribution

        # combine entries for the same nodes
        assert(len(distro) > 0)
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

        # add in any missing nodes from the sender set
        for node_id in self.get_sender_set():
            if node_id not in distro_set:
                distro_set[node_id] = 0.0

        assert(len(distro_set) > 0)
        return distro_set

    def distro_rank_exponetial_backoff(self, rank):
        """Assign distribution value to a given rank position.
        This uses an exponential back off. .5, .25, .125, etc

        Arguments:
            rank {int} -- routing choice rank, starts at 1
        Returns:
            {float} -- Probability this rank is chosen
        """
        return 0.5 ** rank

    def _assign_sender_dist(self, dist_function, node, current_hop_count, prob):
        distro = []
        for child in node.children:
            child_prob = dist_function(child.rank)

            if current_hop_count == 0:
                distro.append((child.data, prob * child_prob))
            else:
                distro.extend(self._assign_sender_dist(dist_function,
                                                       child,
                                                       current_hop_count - 1,
                                                       prob * child_prob))
        return distro

    def _get_node_rank(self, to_node_id, from_node_id, target_address):
        ranked_nodes = self._routing_algorithm(
            from_node_id, target_address, self._nx_graph, self._cache_rank_calculations)
        for i in range(0, len(ranked_nodes)):
            if ranked_nodes[i] == to_node_id:
                return i + 1
        raise Exception('Unable to find path between nodes')

    def _build_tree(self, node_id, current_hop, parent_node, current_path, target_address, override_rank=None):
        if current_hop < 1:
            return

        # check if we already routed through this node
        if node_id in current_path:
            return

        new_path = current_path[:]
        new_path.append(node_id)

        # check to see if an override rank value was supplied
        if override_rank is not None:
            node_rank = override_rank
        else:
            node_rank = self._get_node_rank(
                parent_node.data, node_id, target_address)

        new_node = self._add_child(parent_node, node_id, node_rank)
        if new_node is None:
            return

        if current_hop <= 1:
            return
        # add children node
        for child_id in self._nx_graph.neighbors(node_id):
            self._build_tree(child_id, current_hop - 1,
                             new_node, new_path, target_address)

    def _build_sender_set(self, node_id_list, current_hop_count):
        # needs to search breadth first, otherwise some nodes can be skipped
        if current_hop_count < 1:
            return
        next_node_ids = []
        # add current nodes
        for node_id in node_id_list:
            if node_id in self._sender_set:
                continue
            self._sender_set.add(node_id)

            next_node_ids.extend(self._nx_graph.neighbors(node_id))
        # process next level
        self._build_sender_set(next_node_ids, current_hop_count - 1)

    def _add_child(self, node, child, node_rank):
        '''
        Add new data element to the tree
        :param node: parent node
        :param child: new object to be added
        :return: new node added to the tree
        '''
        if self._max_rank > 0 and node_rank > self._max_rank:
            return None

        level = node.level + 1
        new_entry = RoutingTree._Entry(child, level, node, node_rank)
        node.children.append(new_entry)
        if level not in self._levels:
            self._levels[level] = []
        self._levels[level].append(new_entry)
        return new_entry

    class _Entry(object):
        '''
        Reprents a tree structure
        '''

        def __init__(self, data, level, parent=None, node_rank=1):
            self.data = data
            self.children = []
            self.level = level
            self.parent = parent
            self.rank = node_rank
