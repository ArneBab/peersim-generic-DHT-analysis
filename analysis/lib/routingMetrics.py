# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Routing related metrics
'''
import os
import json
from .tree import RoutingTree


class RoutingMetrics(object):
    '''
    Calculate and store routing related metrics
    '''
    _nx_graphs = {}
    _routing_data_file_name = None

    def __init__(self, graphs, routing_data_file_name):
        if not os.path.exists(routing_data_file_name):
            raise Exception('Could not find the given routing data file')
        self._routing_data_file_name = routing_data_file_name
        self._nx_graphs = graphs

    # def add_route_data(self, data, output_file):
        #'''
        # Add the routing data from a single route
        #:param data: dict that contains the experiment route data
        #'''
        #current_cycle = data['cycle']
        #nx_graph = self._closest_graph(current_cycle)

        # calculate soure and destination difference
        #source_node = nx_graph.node[data['source_node']]
        #destination_node = nx_graph.node[data['destination_node']]
        #x_loc = source_node['location']
        #y_loc = destination_node['location']
        # data['distance'] = min(
        #    [abs(x_loc - y_loc), abs((x_loc + 1) - y_loc), abs(x_loc - (y_loc + 1))])

        #self._calculate_anonymity_set(data, nx_graph)

        # self._route_data.append(data)

    def get_path_length_graph_data(self):
        '''
        Generate histogram graph of the path lengths
        :return: dict of the graph data
        '''
        series_list = ['Routing Path Length', 'Circuit Path Length']
        routing_path_lengths = {}
        circuit_path_length = {}
        for route in self._read_routes():
            length = route['routing_path']['length']
            if length not in routing_path_lengths:
                routing_path_lengths[length] = 0
            routing_path_lengths[length] = routing_path_lengths[length] + 1

            length = route['connection_path']['length']
            if length not in circuit_path_length:
                circuit_path_length[length] = 0
            circuit_path_length[length] = circuit_path_length[length] + 1

        # convert data to histogram data
        largest_r_path = sorted(routing_path_lengths.keys())[-1]
        largest_c_path = sorted(circuit_path_length.keys())[-1]
        max_path = max(largest_r_path, largest_c_path)
        labels = []
        for i in range(1, max_path + 1):
            labels.append(str(i))

        r_data = []
        c_data = []
        for i in range(1, max_path + 1):
            if i in routing_path_lengths:
                r_data.append(routing_path_lengths[i])
            else:
                r_data.append(0)
            
            if i in circuit_path_length:
                c_data.append(circuit_path_length[i])
            else:
                c_data.append(0)

        return {'labels': labels, 'data': [r_data, c_data], 'series': series_list}

    def _calculate_anonymity_set(self, data, nx_graph):
        adversary_node, previous_node = next(
            iter(self._get_adversaries(data)), (None, None))
        if adversary_node is None:
            return

        routing_tree = RoutingTree(
            nx_graph, adversary_node['id'], previous_node['id'], adversary_node['hop'])
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
                adversaries.append((node, previous_node))
            previous_node = node
        return adversaries

    def _closest_graph(self, cycle):
        keys = self._nx_graphs.keys()
        keys.sort()
        previous_key = keys[0]
        for key in keys:
            if key > cycle:
                return self._nx_graphs[previous_key]
            previous_key = key

    def _read_routes(self):
        with open(self._routing_data_file_name) as r_file:
            for data_line in r_file.readlines():
                yield json.loads(data_line)
