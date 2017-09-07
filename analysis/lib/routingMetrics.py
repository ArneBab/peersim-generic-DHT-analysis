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
from .utils import average_degree


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

    def update_routing_data(self, output_file_name):
        '''
        Update the routing data with post experiment metrics
        :param output_file_name: Where to save the new data
        :return: new RoutingMetrics object that uses the updated data file
        '''
        with open(output_file_name, 'w') as r_file:
            for route in self._read_routes():
                self._post_process_route_data(route)
                r_file.write(json.dumps(route))
                r_file.write('\n')

        return RoutingMetrics(self._nx_graphs, output_file_name)

    def get_consolidated_metrics(self):
        '''
        Calculate the experiment wide metrics
        :return: Metrics object
        '''
        metrics = {'avg_degree': None, 'avg_diameter': None, 'avg_node_count': None,
                   'routing_type': None, 'topology_type': None, 'churn_rate': None,
                   'avg_edge_count': None, 'avg_routing_path_length': None,
                   'avg_circuit_path_length': None, 'avg_number_adversary': None,
                   'adversary_messages_intercepted': None, 'adversary_senders_calculable': None,
                   'avg_full_sender_anonymity_set': None, 'avg_sender_anonymity_set': None}

        def avg(x_list): return sum(x_list) / float(len(self._nx_graphs.keys()))

        metrics['avg_degree'] = avg(self._avg_degrees())
        metrics['avg_diameter'] = avg(self._avg_diameters())
        metrics['avg_node_count'] = avg(
            [g.number_of_nodes() for g in self._nx_graphs.values()])
        metrics['avg_edge_count'] = avg(
            [g.number_of_edges() for g in self._nx_graphs.values()])
        adv_count, adv_percent = self._get_number_of_adversaries()
        metrics['avg_number_adversary'] = '%d  (%f%%)' % (
            avg(adv_count), avg(adv_percent))
        return metrics

    def get_graph_stats_over_cycles(self):
        '''
        Generate a graph of the graph metrics
        :return: dict of the graph data
        '''
        series_list = ['Average Degree', 'Graph Diameter']
        labels = []
        data = [[self._avg_diameters()], [self._avg_degrees()]]
        for graph in self._nx_graphs.values():
            labels.append(graph.graph['cycle'])
        return {'labels': labels, 'data': data, 'series': series_list}

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

    def _get_number_of_adversaries(self):
        adversaries_count = []
        adversaries_percent = []
        for graph in self._nx_graphs.values():
            count = len([n for n in graph.node if graph.node[n]['adversary'] == 1])
            adversaries_count.append(count)
            adversaries_percent.append(
                (count / float(graph.number_of_nodes()) * 100))
        return (adversaries_count, adversaries_percent)

    def _avg_diameters(self):
        diameters = []
        for graph in self._nx_graphs.values():
            diameters.append(nx.diameter(graph))
        return diameters

    def _avg_degrees(self):
        degrees = []
        for graph in self._nx_graphs.values():
            degrees.append(average_degree(graph))
        return degrees

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

    def _read_routes(self):
        with open(self._routing_data_file_name) as r_file:
            for data_line in r_file.readlines():
                yield json.loads(data_line)
