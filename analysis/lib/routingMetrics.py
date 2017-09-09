# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Routing related metrics
'''
import os
import json

import networkx as nx

from .tree import RoutingTree
from .utils import average_degree, to_histogram_numbers


class RoutingMetrics(object):
    '''
    Calculate and store routing related metrics
    '''
    _nx_graphs = {}
    _routing_data_file_name = None
    _metrics = {'avg_degree': None, 'avg_diameter': None, 'avg_node_count': None,
                'routing_type': None, 'topology_type': None, 'churn_rate': None,
                'avg_edge_count': None, 'avg_routing_path_length': None,
                'avg_circuit_path_length': None, 'avg_number_adversary': None,
                'adversary_messages_intercepted': None, 'adversary_senders_calculable': None,
                'avg_full_sender_anonymity_set': None, 'avg_sender_anonymity_set': None}
    _avg_diameters = []
    _avg_degrees = []

    def __init__(self, graphs, input_data_file_name, output_data_file_name):
        '''
        Update the routing data with post metrics
        :param graphs: list of networkx graphs
        :param input_data_file_name: Routing data file to read data from
        :param output_data_file_name: new routing data file that is created from the input data file
        '''
        if not os.path.exists(input_data_file_name):
            raise Exception('Could not find the given routing data file')
        self._routing_data_file_name = output_data_file_name
        self._nx_graphs = graphs

        # process routing data and store in new file, use new file as data source then
        with open(self._routing_data_file_name, 'w') as r_file:
            for route in self._read_routes(input_data_file_name):
                self._post_process_route_data(route)
                r_file.write(json.dumps(route))
                r_file.write('\n')

    def calculate_metrics(self):
        '''
        Calculate the experiment wide metrics
        '''

        # helper function for averaging
        def avg(x_list): return sum(x_list) / \
            float(len(self._nx_graphs.keys()))

        # helper function for iterating all graphs
        def all_graphs(op): return [op(g) for g in self._nx_graphs.values()]

        self._avg_degrees = all_graphs(lambda g: average_degree(g))
        self._avg_diameters = all_graphs(lambda g: nx.diameter(g))

        self._metrics['avg_degree'] = avg(self._avg_degrees)
        self._metrics['avg_diameter'] = avg(self._avg_diameters)
        self._metrics['avg_node_count'] = avg(
            [g.number_of_nodes() for g in self._nx_graphs.values()])
        self._metrics['avg_edge_count'] = avg(
            all_graphs(lambda g: g.number_of_edges()))
        adv_count, adv_percent = self._get_number_of_adversaries()
        self._metrics['avg_number_adversary'] = '%d  (%f%%)' % (
            avg(adv_count), avg(adv_percent))

    def get_summary(self):
        '''
        Get the summation metric values
        :return: Dictionary of the metric values
        '''
        return self._metrics

    def graph_metrics(self):
        '''
        Generate a graph of the graph metrics
        :return: dict of the graph data
        '''
        series_list = ['Average Degree', 'Graph Diameter']
        labels = [g.graph['cycle'] for g in self._nx_graphs.values()]
        data = [self._avg_degrees, self._avg_diameters]
        return {'labels': labels, 'data': data, 'series': series_list}

    def graph_path_lengths(self):
        '''
        Generate histogram graph of the path lengths
        :return: dict of the graph data
        '''
        series_list = ['Routing Path Length', 'Circuit Path Length']
        routing_path_lengths = []
        circuit_path_lengths = []
        for route in self._read_routes(self._routing_data_file_name):
            routing_path_lengths.append(route['routing_path']['length'])
            circuit_path_lengths.append(route['connection_path']['length'])

        r_data, start, stop = to_histogram_numbers(routing_path_lengths, 1)
        c_data, start, stop = to_histogram_numbers(circuit_path_lengths, start, stop)
        labels = [str(i) for i in range(1, stop + 1)]

        return {'labels': labels, 'data': [r_data, c_data], 'series': series_list}

    def _get_number_of_adversaries(self):
        adversaries_count = []
        adversaries_percent = []
        for graph in self._nx_graphs.values():
            count = len(
                [n for n in graph.node if graph.node[n]['adversary'] == 1])
            adversaries_count.append(count)
            adversaries_percent.append(
                (count / float(graph.number_of_nodes()) * 100))
        return (adversaries_count, adversaries_percent)

    def _post_process_route_data(self, data):
        #'''
        # Add the routing data from a single route
        #:param data: dict that contains the experiment route data
        #'''
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

    def _calculate_anonymity_set(self, data, nx_graph):
        if 'Ping' not in data['message_type']:
            return
        a_node, p_node = next(
            iter(self._get_adversaries(data)), (None, None))
        if a_node is None:
            return

        r_tree = RoutingTree()
        if r_tree.build(nx_graph, a_node['id'], p_node['id'], a_node['hop']):
            a_set = r_tree.get_data_at_level(r_tree.get_height() - 1)
            data['full_anonymity_set'] = {'length': len(a_set), 'nodes': a_set}

    def _get_adversaries(self, data):
        adversaries = []
        previous_node = None
        for node in data['routing_path']['path']:
            if node['is_adversary']:
                if previous_node is None:
                    raise Exception(
                        'adversary cannot be the source node: %s', str(node))
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
        # return the last one
        return self._nx_graphs[keys[-1]]

    def _read_routes(self, routing_data_file_name):
        with open(routing_data_file_name) as r_file:
            for data_line in r_file.readlines():
                yield json.loads(data_line)
