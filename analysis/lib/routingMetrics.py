# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Routing related metrics
'''
import os
import json

import networkx as nx
import numpy

from .tree import RoutingTree
from .utils import average_degree, to_histogram_numbers
from .configuration import Configuration


class RoutingMetrics(object):
    '''
    Calculate and store routing related metrics
    '''
    _nx_graphs = {}
    _routing_data_file_name = None
    _metrics = {
        'topology_type': None, 'churn_rate': None,
        'sender_anonymity_set_avg': None}
    _avg_diameters = []
    _avg_degrees = []
    _routing_path_lengths = []
    _circiut_path_lengths = []
    _anon_set_size_full = []
    _message_count = 0
    _message_inter_count = 0
    _message_inter_pro_count = 0
    _adversary_inter_hop = []

    def __init__(self, graphs, input_data_file_name, output_data_file_name, experiment_config):
        '''
        Update the routing data with post metrics
        :param graphs: list of networkx graphs
        :param input_data_file_name: Routing data file to read data from
        :param output_data_file_name: new routing data file that is created from the input data file
        :param experiment_config: experiment configuration
        '''
        if not os.path.exists(input_data_file_name):
            raise Exception('Could not find the given routing data file')
        self._routing_data_file_name = output_data_file_name
        self._nx_graphs = graphs
        for param in Configuration.get_parameters():
            self._metrics['X: ' +
                          param] = self._wrapper(experiment_config[param])

        # process routing data and store in new file, use new file as data source then
        with open(self._routing_data_file_name, 'w') as r_file:
            for route in self._read_routes(input_data_file_name):
                self._post_process_route_data(route)

                r_file.write(json.dumps(route))
                r_file.write('\n')

                # lengths
                self._routing_path_lengths.append(
                    route['routing_path']['length'])
                self._circiut_path_lengths.append(
                    route['connection_path']['length'])

                # counters
                self._message_count = self._message_count + 1
                if 'full_anonymity_set' in route:
                    self._message_inter_count = self._message_inter_count + 1
                    self._adversary_inter_hop.append(route['full_anonymity_set']['hop'])

                    if route['full_anonymity_set']['calculated']:
                        self._message_inter_pro_count = self._message_inter_pro_count + 1
                        self._anon_set_size_full.append(
                            route['full_anonymity_set']['length'])

    def calculate_metrics(self):
        '''
        Calculate the experiment wide metrics
        '''

        # helper function for iterating all graphs
        def all_graphs(op): return [op(g) for g in self._nx_graphs.values()]

        def per(sel, tot): return (sel / float(tot)) * 100

        def w(v, d=None): return self._wrapper(v, d)

        self._avg_degrees = all_graphs(lambda g: average_degree(g))
        self._avg_diameters = all_graphs(lambda g: nx.diameter(g))

        self._metrics['degree_avg'] = w(numpy.mean(self._avg_degrees))
        self._metrics['degree_std'] = w(numpy.std(self._avg_degrees))

        self._metrics['diameter_avg'] = w(numpy.mean(self._avg_diameters))
        self._metrics['diameter_std'] = w(numpy.std(self._avg_diameters))

        node_counts = [g.number_of_nodes() for g in self._nx_graphs.values()]
        self._metrics['node_count_avg'] = w(numpy.mean(node_counts))
        self._metrics['node_count_std'] = w(numpy.std(node_counts))

        edge_counts = all_graphs(lambda g: g.number_of_edges())
        self._metrics['edge_count_avg'] = w(numpy.mean(edge_counts))
        self._metrics['edge_count_std'] = w(numpy.std(edge_counts))

        adv_count, adv_percent = self._get_number_of_adversaries()
        self._metrics['adversary_count_avg'] = w(numpy.mean(
            adv_count), '(%f%% of all nodes)' % numpy.mean(adv_percent))
        self._metrics['adversary_count_std'] = w(numpy.std(adv_count))

        self._metrics['adversary_messages_intercepted'] = w(
            self._message_inter_count, '(%f%% of all messages)' %
            per(self._message_inter_count, self._message_count)
        )
        self._metrics['adversary_messages_intercepted_percent'] = w(
            per(self._message_inter_count, self._message_count))

        self._metrics['adversary_senders_calculable'] = w(
            self._message_inter_pro_count,
            '(%f%% of intercepted messages) (%f%% of all messages)' %
            (per(self._message_inter_pro_count, self._message_inter_count),
             per(self._message_inter_pro_count, self._message_count))
        )
        self._metrics['adversary_senders_calculable_percent_of_intercepted'] = w(
            per(self._message_inter_pro_count, self._message_inter_count))
        self._metrics['adversary_senders_calculable_percent_of_total'] = w(
            per(self._message_inter_pro_count, self._message_count))

        self._metrics['message_count'] = w(self._message_count)

        self._metrics['path_length_routing_avg'] = w(numpy.mean(
            self._routing_path_lengths))
        self._metrics['path_length_routing_std'] = w(numpy.std(
            self._routing_path_lengths))

        self._metrics['path_length_circuit_avg'] = w(numpy.mean(
            self._circiut_path_lengths))
        self._metrics['path_length_circuit_std'] = w(numpy.std(
            self._circiut_path_lengths))

        self._metrics['sender_anonymity_set_full_avg'] = w(
            numpy.mean(self._anon_set_size_full))
        self._metrics['sender_anonymity_set_full_std'] = w(
            numpy.std(self._anon_set_size_full))

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

    def graph_anonymity_set(self):
        '''
        Generate a graph of the anonymity set sizes
        :return: dict of graph data
        '''
        series_list = ['Sender Set Size']
        data, start, stop = to_histogram_numbers(self._anon_set_size_full, 1)
        labels = [str(i) for i in range(start, stop + 1)]
        return {'labels': labels, 'data': data, 'series': series_list}

    def graph_intercept_hop(self):
        '''
        Generate a graph of where adversaries intercepted a message
        :return: dict of graph data
        '''
        series_list = ['Adversary Intercept Hop']
        data, start, stop = to_histogram_numbers(self._adversary_inter_hop, 0)
        labels = [str(i) for i in range(start, stop + 1)]
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
        c_data, start, stop = to_histogram_numbers(
            circuit_path_lengths, start, stop)
        labels = [str(i) for i in range(1, stop + 1)]

        return {'labels': labels, 'data': [r_data, c_data], 'series': series_list}

    def _wrapper(self, value, description=None):
        return {'value': value, 'description': description}

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
            a_data = {'calculated': True, 'length': len(a_set),
                      'nodes': a_set, 'estimated_work': r_tree.estimated_work,
                      'hop': a_node['hop']}
        else:
            a_data = {'calculated': False, 'length': 0, 'hop': a_node['hop'],
                      'nodes': [], 'estimated_work': r_tree.estimated_work}
        data['full_anonymity_set'] = a_data

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
