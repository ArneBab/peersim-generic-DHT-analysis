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

    def __init__(self, nx_graph, routing_algorithm, max_length=0):
        """Constructor

        Arguments:
            nx_graph {Graph} -- Topology graph
            routing_algorithm {function} -- Routing algorithm used by protocol

        Keyword Arguments:
            max_rank {int} -- Maximum rank of nodes to calculate
            a path for from each node. Top nodes will be followed. (default: {2})
            max_length {int} -- Maximum number of hops to calculate routing paths.
            (default: {0})
        """
        self._root = None
        self._levels = {}
        self._sender_set = set()
        self._cache_rank_calculations = {}

        self._nx_graph = nx_graph
        self._routing_algorithm = routing_algorithm
        self._max_length = max_length

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

        if self._max_length > 0 and max_hop > self._max_length:
            return False

        # calculate the sender set
        self._sender_set.add(adversary_node_id)
        self._build_sender_set([previous_node_id], max_hop)
        self._sender_set.remove(adversary_node_id)

        # calculate the preferred routing paths
        self._root = RoutingTree._Entry(adversary_node_id, 0)
        self._levels[0] = [self._root]
        prev_node = self._add_child(self._root, previous_node_id, 1)
        self._build_tree([prev_node], max_hop, target_address)

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
        return len(self._levels.keys())

    def get_sender_set(self):
        '''
        Return the list of the sender set
        :return: Unique list of senders
        '''
        # its dumb, set is not json serializable so turn it back into a list
        return list(self._sender_set)

    def get_sender_set_rank(self):
        """Calculate the rank of the sender set

        Returns:
            dict -- Dict of the sender set nodes keyed by rank,
            each entry is a list of nodes
        """
        if self.get_height() < 2:
            return {}
        if self.get_height() == 2:
            return {1: [self._root.children[0].data]}
        # known its 100% for the level 1 node (previous), so we can skip

        # use rank value instead of a distribution
        def dist_function(rank): return rank

        def add_function(a, b): return a + b

        # assign distribution
        ranks = self._assign_sender_dist(
            dist_function, self._root.children[0], self.get_height() - 3, 1, add_function)
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

    def get_sender_set_distribution_full(self):
        """Calculate the probability distribution only using the sender set

        Returns:
            dict -- Dict with key of node id and value of normalized probability
        """
        sender_set = self.get_sender_set()
        distro_set = {}
        total = len(sender_set)
        for node in sender_set:
            distro_set[node] = 1.0 / + total

        return distro_set

    def get_sender_set_distribution_by_top_rank(self):
        """Calculate the probability distribution for the sender set using top rank

        Returns:
            dict -- Dict with key of node id and value of normalized probability
        """
        ranked = self.get_sender_set_rank()
        if len(ranked) <= 0:
            return {}

        top_rank = sorted(ranked.keys())[0]

        distro_set = {}
        total = len(ranked[top_rank])
        for node in ranked[top_rank]:
            distro_set[node] = 1.0 / + total

        # add in any missing nodes from the sender set
        for node_id in self.get_sender_set():
            if node_id not in distro_set:
                distro_set[node_id] = 0.0

        assert(len(distro_set) > 0)
        return distro_set

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

        def mult(a, b): return a * b

        distro = self._assign_sender_dist(
            dist_function, self._root.children[0], self.get_height() - 3, 1, mult)

        # every node in the sender set and not in this distribution set has a probability of zero
        # Don't need to add these since they will not affect the final probability distribution

        assert(len(distro) > 0)

        # combine entries for the same nodes
        distro_set = {}
        total = 0.0
        for node, prob in distro:
            if node not in distro_set:
                distro_set[node] = 0
            distro_set[node] = distro_set[node] + prob
            total = total + prob

        # normalize the distributions (e.g. their sum == 1)
        if total > 0.0:
            # only run if a clear path was found
            for node, prob in distro_set.items():
                distro_set[node] = prob / total
        else:
            # add all nodes with equal distribution
            for node_id in self.get_sender_set():
                distro_set[node_id] = 1.0 / len(self.get_sender_set())

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

    def to_bracket(self):
        """Return the bracket representation of the tree

        Returns:
            string -- String bracket representation of this tree
        """
        return self._to_bracket(self._root)

    def _to_bracket(self, node):
        if node is None:
            return ''
        bracket_str = '({}--{}'.format(node.data, node.rank)
        for child in node.children:
            bracket_str += self._to_bracket(child)
        return bracket_str + ')'

    def _assign_sender_dist(self, dist_function, node, current_hop_count, prob, action):
        distro = []
        for child in node.children:
            child_prob = dist_function(child.rank)

            combined_prob = action(prob, child_prob)

            if current_hop_count == 0:
                distro.append((child.data, combined_prob))
            else:
                distro.extend(self._assign_sender_dist(dist_function,
                                                       child,
                                                       current_hop_count - 1,
                                                       combined_prob,
                                                       action))
        return distro

    def _get_node_rank(self, to_node_id, from_node_id, target_address):
        ranked_nodes = self._routing_algorithm(
            from_node_id, target_address, self._nx_graph, self._cache_rank_calculations)
        for i in range(0, len(ranked_nodes)):
            if to_node_id in ranked_nodes[i]:
                return i + 1
        raise Exception('Unable to find path between nodes')

    def _build_tree(self, node_list, max_hop, target_address):
        last_max_hop = 1
        while True:
            # try to build with only rank #1
            new_nodes = self._build_tree_routes(
                node_list, max_hop, target_address)
            if len(new_nodes) > 0:
                # reset the max hop to 1
                last_max_hop = 1

            if self.get_height() > max_hop:
                return
            # didn't build a complete path
            # add next rank to all existing nodes
            last_max_hop += 1
            all_nodes = self._get_all_nodes()
            added_nodes = []
            for node in all_nodes:
                added_nodes.extend(self._build_tree_routes_node(
                    node, target_address, last_max_hop))

            if len(added_nodes) > 0:
                # reset the max hop to 1
                last_max_hop = 1
            # only need to start building the tree from the new added nodes
            node_list = added_nodes

    def _get_all_nodes(self):
        all_nodes = []
        for level, values in self._levels.items():
            if level == 0:
                continue
            all_nodes.extend(values)
        return all_nodes

    def _build_tree_routes(self, node_list, max_hops, target_address):
        process_nodes = node_list
        all_nodes_added = []
        while len(process_nodes) > 0:
            added_leaves = []
            for node in process_nodes:
                if node.level >= max_hops:
                    continue
                new_nodes = self._build_tree_routes_node(
                    node, target_address, 1)
                added_leaves.extend(new_nodes)
                all_nodes_added.extend(new_nodes)
            process_nodes = added_leaves
        return all_nodes_added

    def _build_tree_routes_node(self, node, target_address, max_rank):
        added_children = []
        path = node.get_path()
        children_ids = node.get_child_ids()
        for child_id in self._nx_graph.neighbors(node.data):
            if child_id in path:
                continue
            if child_id in children_ids:
                continue
            rank = self._get_node_rank(node.data, child_id, target_address)
            if rank <= max_rank:
                added_children.append(self._add_child(node, child_id, rank))
        return added_children

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

        def get_path(self):
            path = []
            walker = self
            while walker is not None:
                path.insert(0, walker.data)
                walker = walker.parent
            return path

        def get_child_ids(self):
            child_ids = []
            for child in self.children:
                child_ids.append(child.data)
            return child_ids

        def __repr__(self):
            return str(self.data)
