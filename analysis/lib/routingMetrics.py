# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Routing related metrics
'''
from .tree import RoutingTree


class RoutingMetrics(object):
    '''
    Calculate and store routing related metrics
    '''
    _nx_graphs = {}
    _route_data = {}

    def __init__(self, grpahs):
        self._nx_graphs = grpahs
        self._route_data = {}

    def add_route_data(self, data):
        '''
        Add the routing data from a single route
        :param data: dict that contains the experiment route data
        '''
        current_cycle = data['cycle']
        nx_graph = self._closest_graph(current_cycle)

        # calculate soure and destination difference
        source_node = nx_graph.node[data['source_node']]
        destination_node = nx_graph.node[data['destination_node']]
        x_loc = source_node['location']
        y_loc = destination_node['location']
        data['distance'] = min(
            [abs(x_loc - y_loc), abs((x_loc + 1) - y_loc), abs(x_loc - (y_loc + 1))])

        self._calculate_anonymity_set(data, nx_graph)

        self._route_data[current_cycle] = data

    def _calculate_anonymity_set(self, data, nx_graph):
        adversary_id, previous_id = next(
            iter(self._get_adversaries(data)), (None, None))
        if adversary_id is None:
            return

        routing_tree = RoutingTree(
            nx_graph, adversary_id, previous_id, data['hop'])
        full_anonymity_set = routing_tree.get_data_at_level(
            routing_tree.get_height() - 1)
        thing = 1

    def _get_adversaries(self, data):
        adversaries = []
        previous_node = None
        for node in data['routing_path']['path']:
            if node['is_adversary']:
                if previous_node is None:
                    raise Exception('adversary cannot be the source node')
                adversaries.append((node['id'], previous_node['id']))
            previous_node = node
        return adversaries

    def _closest_graph(self, cycle):
        keys = self._nx_graphs.keys()
        keys.sort()
        for key in keys:
            if key >= cycle:
                return self._nx_graphs[key]
