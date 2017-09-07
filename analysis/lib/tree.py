# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Class for storing and building potentical routing trees
'''
import logging
import math
from .utils import average_degree


class RoutingTree(object):
    '''
    Represents a potential routing tree traced back from start node
    '''
    _root = None
    _levels = {}

    def build(self, nx_graph, start_node_id, previous_node_id, max_hop, work_check=True):
        '''
        Build the routing tree
        :param nx_graph: networkx graph
        :param start_node_id: The first node the routing paths start from
        :param previous_node_id: The previous node is always known, so record it
        :param max_hop: How many hops to buld the routing table to
        :return: True if the tree was calculate; otherwise False
        '''
        self._root = RoutingTree._Entry(start_node_id, 0)
        self._levels = {}
        self._levels[0] = [self._root]
        previous_node = self._add_child(self._root, previous_node_id)

        # estimate work load
        estimated_work = self._estimate_nodes_in_tree(nx_graph, max_hop)
        logging.info('%d : Estimated work load for anonymity set',
                     estimated_work)
        if work_check and estimated_work > nx_graph.number_of_nodes() * 2:
            logging.info('Not calculating anonymity set too large')
            return False

        # add the rest of the tree
        for child_id in nx_graph.neighbors(previous_node_id):
            self._build_tree(nx_graph, child_id, max_hop - 1,
                             previous_node, [start_node_id, previous_node_id])

        logging.info('%d : Actual work anonymity set work', self.get_count())
        return True

    def get_data_at_level(self, level):
        '''
        Get all inserted data at a given level
        :param level: Zero based index, can be a positive or
            negative reference to the level
        :return: list of data at that level
        '''
        if abs(level) not in self._levels:
            raise Exception('Out of bound index')
        return [i.data for i in self._levels[abs(level)]]

    def get_height(self):
        '''
        Height of the tree
        :return: int count of the number of levels
        '''
        return len(self._levels.keys())

    def get_count(self):
        '''
        Count the number of nodes in the tree
        :return: int count
        '''
        return self._get_count(self._root) + 1

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
