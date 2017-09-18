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
from .utils import average_degree, to_histogram_ints, to_histogram_floats
from .utils import distance, entropy_normalized
from .configuration import Configuration


class RoutingMetrics(object):
    '''
    Calculate and store routing related metrics
    '''
    _nx_graphs = {}
    _routing_data_file_name = None
    _metrics = {
        'missing': {'churn_rate': None}}

    ##########################################
    class RawMetrics(object):
        ''' Class stores Raw metric data '''
        avg_diameters = []
        avg_degrees = []
        routing_path_lengths = []
        circiut_path_lengths = []
        sender_set_size = []
        message_count = 0
        message_inter_count = 0
        message_inter_pro_count = 0
        adv_inter_hop = []
        adv_inter_hop_calced = []
        anon_entropy = []
        anon_top_rank_set_size = []
        anon_top_rank = []
        anon_top_rank_correct_count = 0
        anon_rank_missing_count = 0
        anon_rank_diff_actual = []
        anon_entropy_missing_count = 0

        def to_dict(self):
            ''' Returns the classes variables and values in dict '''
            myself = {}
            for name in dir(self):
                if name.startswith('_'):
                    continue
                value = getattr(self, name)
                if callable(value):
                    continue
                myself[name] = value
            return myself
    _raw = RawMetrics()
    ##########################################

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
        parameters = {}
        for param in Configuration.get_parameters():
            if param in experiment_config:
                parameters[param] = self._wrapper(
                    experiment_config[param])
        self._metrics['variables'] = parameters

        # process routing data and store in new file, use new file as data source then
        with open(self._routing_data_file_name, 'w') as r_file:
            for route in self._read_routes(input_data_file_name):
                self._post_process_route_data(route, experiment_config)

                r_file.write(json.dumps(route))
                r_file.write('\n')

                # lengths
                self._raw.routing_path_lengths.append(
                    route['routing_path']['length'])
                self._raw.circiut_path_lengths.append(
                    route['connection_path']['length'])

                # counters
                self._raw.message_count += 1
                if 'anonymity_set' in route:
                    self._raw.message_inter_count += 1
                    self._raw.adv_inter_hop.append(
                        route['anonymity_set']['hop'])

                    if route['anonymity_set']['calculated']:
                        self._raw.message_inter_pro_count += + 1
                        self._raw.sender_set_size.append(
                            route['anonymity_set']['full_set']['length'])
                        self._raw.adv_inter_hop_calced.append(
                            route['anonymity_set']['hop'])

                        prob_dict = route['anonymity_set']['probability_set']
                        self._raw.anon_entropy.append(entropy_normalized(
                            prob_dict.values()))

                        ranked_set = route['anonymity_set']['ranked_set']
                        top_rank = sorted(ranked_set.keys())[0]
                        self._raw.anon_top_rank_set_size.append(
                            len(ranked_set[top_rank]))
                        self._raw.anon_top_rank.append(top_rank)

                        if route['source_node'] not in prob_dict.keys():
                            self._raw.anon_entropy_missing_count += 1

                        diff = self._ranked_nodes_diff(
                            ranked_set, route['source_node'])
                        if diff < 0:
                            self._raw.anon_rank_missing_count += 1
                        else:
                            if diff == 0:
                                self._raw.anon_top_rank_correct_count += 1
                            self._raw.anon_rank_diff_actual.append(diff)

    def calculate_metrics(self):
        '''
        Calculate the experiment wide metrics
        '''

        # helper function for iterating all graphs
        def all_graphs(op): return [op(g) for g in self._nx_graphs.values()]

        def per(sel, tot):
            if tot == 0:
                return 0.0
            return sel / float(tot)

        def w(v, d=None): return self._wrapper(v, d)

        self._raw.avg_degrees = all_graphs(lambda g: average_degree(g))
        self._raw.avg_diameters = all_graphs(lambda g: nx.diameter(g))

        ##################################################################
        self._metrics['graph'] = {}
        self._metrics['graph']['degree_avg'] = w(
            numpy.mean(self._raw.avg_degrees))
        self._metrics['graph']['degree_std'] = w(
            numpy.std(self._raw.avg_degrees))

        self._metrics['graph']['diameter_avg'] = w(
            numpy.mean(self._raw.avg_diameters))
        self._metrics['graph']['diameter_std'] = w(
            numpy.std(self._raw.avg_diameters))

        node_counts = [g.number_of_nodes() for g in self._nx_graphs.values()]
        self._metrics['graph']['node_count_avg'] = w(numpy.mean(node_counts))
        self._metrics['graph']['node_count_std'] = w(numpy.std(node_counts))

        edge_counts = all_graphs(lambda g: g.number_of_edges())
        self._metrics['graph']['edge_count_avg'] = w(numpy.mean(edge_counts))
        self._metrics['graph']['edge_count_std'] = w(numpy.std(edge_counts))

        ##################################################################
        self._metrics['adversary'] = {}
        adv_count, adv_percent = self._get_number_of_adversaries()
        self._metrics['adversary']['count_avg'] = w(numpy.mean(
            adv_count), '(%f%% of all nodes)' % numpy.mean(adv_percent))
        self._metrics['adversary']['count_std'] = w(numpy.std(adv_count))

        self._metrics['adversary']['messages_intercepted'] = w(
            self._raw.message_inter_count)
        if self._raw.message_inter_count > 0:
            percent = per(self._raw.message_inter_count,
                          self._raw.message_count)
            self._metrics['adversary']['messages_intercepted_percent'] = w(
                percent, '%f%%' % (percent * 100))

        self._metrics['adversary']['sender_sets_calculable'] = w(
            self._raw.message_inter_pro_count)
        if self._raw.message_inter_pro_count > 0:
            percent = per(self._raw.message_inter_pro_count,
                          self._raw.message_inter_count)
            self._metrics['adversary']['sender_sets_calculable_percent_of_intercepted'] = w(
                percent, '%f%%' % (percent * 100))
            percent = per(self._raw.message_inter_pro_count,
                          self._raw.message_count)
            self._metrics['adversary']['sender_sets_calculable_percent_of_total'] = w(
                percent, '%f%%' % (percent * 100))

        ##################################################################
        self._metrics['routing'] = {}
        self._metrics['routing']['message_count'] = w(self._raw.message_count)

        self._metrics['routing']['path_length_routing_avg'] = w(numpy.mean(
            self._raw.routing_path_lengths))
        self._metrics['routing']['path_length_routing_std'] = w(numpy.std(
            self._raw.routing_path_lengths))

        self._metrics['routing']['path_length_circuit_avg'] = w(numpy.mean(
            self._raw.circiut_path_lengths))
        self._metrics['routing']['path_length_circuit_std'] = w(numpy.std(
            self._raw.circiut_path_lengths))

        ##################################################################
        self._metrics['anonymity'] = {}
        if len(self._raw.sender_set_size) > 0:
            self._metrics['anonymity']['sender_set_size_avg'] = w(
                numpy.mean(self._raw.sender_set_size))
            self._metrics['anonymity']['sender_set_size_std'] = w(
                numpy.std(self._raw.sender_set_size))
            self._metrics['anonymity']['entropy_avg'] = w(
                numpy.mean(self._raw.anon_entropy))
            self._metrics['anonymity']['entropy_std'] = w(
                numpy.std(self._raw.anon_entropy))
            self._metrics['anonymity']['top_rank_set_size_avg'] = w(
                numpy.mean(self._raw.anon_top_rank_set_size))
            self._metrics['anonymity']['top_rank_set_size_std'] = w(
                numpy.std(self._raw.anon_top_rank_set_size))
            self._metrics['anonymity']['top_rank_value_avg'] = w(
                numpy.mean(self._raw.anon_top_rank))
            self._metrics['anonymity']['top_rank_value_std'] = w(
                numpy.std(self._raw.anon_top_rank))

            ##############################################################
            self._metrics['anonymity_accuracy'] = {}
            self._metrics['anonymity_accuracy']['entropy_missed_actual_source'] = w(
                self._raw.anon_entropy_missing_count)
            percent = per(self._raw.anon_entropy_missing_count,
                          self._raw.message_inter_pro_count)
            self._metrics['anonymity_accuracy']['entropy_missed_actual_source_percent'] = w(
                percent, '%f%%' % (percent * 100))

            self._metrics['anonymity_accuracy']['ranked_missed_actual_source'] = w(
                self._raw.anon_rank_missing_count)
            percent = per(self._raw.anon_rank_missing_count,
                          self._raw.message_inter_pro_count)
            self._metrics['anonymity_accuracy']['ranked_missed_actual_source_percent'] = w(
                percent, '%f%%' % (percent * 100))

            self._metrics['anonymity_accuracy']['rank_diff_from_actual_avg'] = w(
                numpy.mean(self._raw.anon_rank_diff_actual))
            self._metrics['anonymity_accuracy']['rank_diff_from_actual_std'] = w(
                numpy.std(self._raw.anon_rank_diff_actual))

            self._metrics['anonymity_accuracy']['top_rank_correct'] = w(
                self._raw.anon_top_rank_correct_count)
            percent = per(self._raw.anon_top_rank_correct_count,
                          self._raw.message_inter_pro_count)
            self._metrics['anonymity_accuracy']['top_rank_correct_percent'] = w(
                percent, '%f%%' % (percent * 100))

        ##################################################################
        self._metrics['_raw'] = self._raw.to_dict()

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
        data = [self._raw.avg_degrees, self._raw.avg_diameters]
        return {'labels': labels, 'data': data, 'series': series_list}

    def graph_sender_set(self):
        '''
        Generate a graph of the sender set sizes
        :return: dict of graph data
        '''
        series_list = ['Sender Set Size']
        labels, data, start, stop = to_histogram_ints(
            self._raw.sender_set_size, 1)
        return {'labels': labels, 'data': data, 'series': series_list}

    def graph_sender_set_by_hop(self):
        '''
        Generate a graph of the sender set sizes by intercepted at hop
        :return: dict of graph data
        '''
        series_list = ['Sender Set Size Average',
                       'Sender Set Size Standard Deviation']
        return self._graph_by_hop(series_list,
                                  self._raw.adv_inter_hop_calced,
                                  self._raw.sender_set_size)

    def graph_entropy(self):
        '''
        Generate a graph histogram of the entropy values by .05
        :return: dict of graph data
        '''
        series_list = ['Entropy']

        def _bucket(x):
            whole = int(x * 100)
            whole_bin = (whole / 5) * 5
            return whole_bin / 100.0
        labels, data, start, stop = to_histogram_floats(
            self._raw.anon_entropy, 0.05, 2, 0.0, 1.0, _bucket)
        return {'labels': labels, 'data': data, 'series': series_list}

    def graph_entropy_by_hop(self):
        '''
        Generate a graph avg entropy by intercepted at hop
        :return: dict of graph data
        '''
        series_list = ['Entropy Average',
                       'Entropy Standard Deviation']

        return self._graph_by_hop(series_list,
                                  self._raw.adv_inter_hop_calced,
                                  self._raw.anon_entropy)

    def graph_top_rank_set_size_by_hop(self):
        '''
        Generate a graph avg top rank set size by intercepted at hop
        :return: dict of graph data
        '''
        series_list = ['Top Rank Set Size Average',
                       'Top Rank Set Size Standard Deviation']

        return self._graph_by_hop(series_list,
                                  self._raw.adv_inter_hop_calced,
                                  self._raw.anon_top_rank_set_size)

    def graph_top_rank_by_hop(self):
        '''
        Generate a graph avg top rank value by intercepted at hop
        :return: dict of graph data
        '''
        series_list = ['Top Rank Average',
                       'Top Rank Standard Deviation']

        return self._graph_by_hop(series_list,
                                  self._raw.adv_inter_hop_calced,
                                  self._raw.anon_top_rank)

    def graph_intercept_hop(self):
        '''
        Generate a graph of where adversaries intercepted a message
        :return: dict of graph data
        '''
        series_list = ['Adversary Intercept Hop']
        labels, data, start, stop = to_histogram_ints(
            self._raw.adv_inter_hop, 1)
        return {'labels': labels, 'data': data, 'series': series_list}

    def graph_intercept_hop_calculated(self):
        '''
        Generate a graph of where adversaries intercepted a message
        :return: dict of graph data
        '''
        series_list = ['Adversary Intercept Hop for Calculated']
        labels, data, start, stop = to_histogram_ints(
            self._raw.adv_inter_hop_calced, 1)
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

        labels, r_data, start, stop = to_histogram_ints(
            routing_path_lengths, 1)
        labels, c_data, start, stop = to_histogram_ints(
            circuit_path_lengths, start, stop)

        return {'labels': labels, 'data': [r_data, c_data], 'series': series_list}

    def _wrapper(self, value, description=None):
        return {'value': value, 'description': description}

    def _graph_by_hop(self, series_list, hop_list, data_list):
        # organize data into buckets
        if len(hop_list) != len(data_list):
            raise Exception('Something is very wrong, not the same length')

        holder = {}
        max_hop = 0
        for i in range(0, len(data_list)):
            data = data_list[i]
            hop = hop_list[i]
            if hop not in holder:
                holder[hop] = []
            holder[hop].append(data)
            if hop > max_hop:
                max_hop = hop

        # write data into graph format
        avg_data = []
        std_data = []
        labels = []
        for i in range(0, max_hop):
            hop = i + 1
            labels.append(hop)
            if hop in holder:
                avg_data.append(numpy.mean(holder[hop]))
                std_data.append(numpy.std(holder[hop]))
            else:
                avg_data.append(0)
                std_data.append(0)

        return {'labels': labels, 'data': [avg_data, std_data], 'series': series_list}

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

    def _post_process_route_data(self, data, parameters):
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
        data['distance'] = distance(x_loc, y_loc)

        self._calculate_anonymity_set(data, nx_graph, parameters)

    def _calculate_anonymity_set(self, data, nx_graph, parameters):
        if 'Ping' not in data['message_type']:
            return
        a_node, p_node = next(
            iter(self._get_adversaries(data)), (None, None))
        if a_node is None:
            return

        r_tree = RoutingTree()
        if r_tree.build(nx_graph, a_node['id'], p_node['id'], a_node['hop']):
            a_data = {'calculated': True, 'estimated_work': r_tree.estimated_work,
                      'hop': a_node['hop']}
            a_set = r_tree.get_sender_set()
            a_data['full_set'] = {'length': len(a_set), 'nodes': a_set}

            # map routing type to ranking algorithm
            if parameters['router_type'] == 'DHTRouterGreedy':
                route_alg = r_tree.rank_greedy
            else:
                raise Exception('Unknown routing type')

            a_data['ranked_set'] = r_tree.get_sender_set_rank(
                route_alg, data['target'])
            a_data['probability_set'] = r_tree.get_sender_set_distribution(
                route_alg, r_tree.distro_rank_exponetial_backoff, data['target'])
        else:
            a_data = {'calculated': False,
                      'hop': a_node['hop'], 'estimated_work': r_tree.estimated_work}
        data['anonymity_set'] = a_data

    def _ranked_nodes_diff(self, ranked_set, source_node_id):
        sorted_rank = sorted(ranked_set.keys())
        top_rank = sorted_rank[0]
        for rank in sorted_rank:
            if source_node_id in ranked_set[rank]:
                return rank - top_rank
        return -1

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
