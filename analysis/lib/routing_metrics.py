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
from .utils import distance, entropy_normalized, entropy, max_entropy, timeit
from .configuration import Configuration


class RoutingMetrics(object):
    '''
    Calculate and store routing related metrics
    '''
    ##########################################
    class RawMetrics(object):
        ''' Class stores Raw metric data '''

        def __init__(self):
            self.parameters = {}
            self.avg_diameters = []
            self.avg_degrees = []
            self.routing_path_lengths = []
            self.circiut_path_lengths = []
            self.sender_set_size = []
            self.message_count = 0
            self.message_inter_count = 0
            self.message_inter_pro_count = 0
            self.adv_inter_hop = []
            self.adv_inter_hop_calced = []
            self.anon_entropy_max = []
            self.anon_entropy = []
            self.anon_entropy_actual = []
            self.anon_entropy_actual_max = []
            self.anon_entropy_norm = []
            self.anon_entropy_norm_actual = []
            self.anon_top_rank_set_size = []
            self.anon_top_rank = []
            self.anon_top_rank_correct_count = 0
            self.anon_rank_missing_count = 0
            self.anon_rank_diff_actual = []
            self.anon_entropy_missing_count = 0
            self.anon_entropy_best_hit = 0
            self.anon_entropy_best_diff = []
            self.anon_entropy_actual_best_hit = 0
            self.anon_entropy_actual_best_diff = []

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

        def set(self, key, value):
            '''
            Set the current value of a given configuration parameter
            :param key: parameter name
            :param value: value to assign to the parameter
            '''
            setattr(self, key, value)

        def get(self, key):
            '''
            Get the current value of a given configuration parameter
            :param key: parameter name
            :return: Value assigned to the configuration parameter
            '''
            return getattr(self, key)

    ##########################################

    #@timeit
    def __init__(self, graphs, experiment_config_list, routing_choice_avg=None,
                 input_data_file_name=None, output_data_file_name=None):
        '''
        Update the routing data with post metrics
        :param graphs: dict of networkx graphs
        :param input_data_file_name: Routing data file to read data from
        :param output_data_file_name: new routing data file that is created from the input data file
        :param experiment_config: experiment configuration
        '''
        self._raw = RoutingMetrics.RawMetrics()
        self._nx_graphs = graphs
        self._metrics = {}

        if input_data_file_name:
            self._init_full(experiment_config_list, routing_choice_avg,
                            input_data_file_name, output_data_file_name)
        else:
            self._init_load(experiment_config_list)

    def _init_load(self, experiment_config_list):
        parameters = {}
        for param in Configuration.get_parameters():
            if param == 'repeat':
                continue
            if param in experiment_config_list[0]:
                parameters[param] = self._wrapper(
                    experiment_config_list[0][param], param)
        self._metrics['variables'] = parameters

        for exp_config in experiment_config_list:
            base_directory = os.path.dirname(exp_config['routing_data_path'])
            raw_data_file = os.path.join(base_directory, 'metrics', 'consolidated.json')
            with open(raw_data_file, 'r') as r_file:
                raw_metrics = json.loads(r_file.read())['_raw']
            for name, metric in raw_metrics.items():
                if isinstance(metric, list):
                    self._raw.get(name).extend(metric)
                elif isinstance(metric, dict):
                    self._raw.set(name, metric)
                else:
                    self._raw.set(name, self._raw.get(name) + metric)

    def _init_full(self, experiment_config_list, routing_choice_avg,
                   input_data_file_name, output_data_file_name):
        ''' Load a single experiment '''
        experiment_config = experiment_config_list[0]
        if not os.path.exists(input_data_file_name):
            raise Exception('Could not find the given routing data file')

        parameters = {}
        for param in Configuration.get_parameters():
            if param in experiment_config:
                parameters[param] = self._wrapper(
                    experiment_config[param], param)
        self._metrics['variables'] = parameters
        self._raw.parameters = experiment_config.copy()

        # process routing data and store in new file, use new file as data source then
        with open(output_data_file_name, 'w') as r_file:
            for route in self._read_routes(input_data_file_name):
                self._post_process_route_data(
                    route, experiment_config, routing_choice_avg)

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
                        self._raw.anon_entropy.append(entropy(
                            prob_dict.values()))
                        self._raw.anon_entropy_max.append(max_entropy(
                            prob_dict.values()))
                        self._raw.anon_entropy_norm.append(entropy_normalized(
                            prob_dict.values()))
                        # how did entropy do?
                        if route['source_node'] not in prob_dict.keys():
                            self._raw.anon_entropy_missing_count += 1
                        else:
                            best_prob = sorted(prob_dict.values())[-1]
                            diff = best_prob - prob_dict[route['source_node']]
                            self._raw.anon_entropy_best_diff.append(diff)
                            if diff == 0.0:
                                self._raw.anon_entropy_best_hit += 1

                        prob_dict_act = route['anonymity_set']['probability_set_actual']
                        self._raw.anon_entropy_actual.append(entropy(
                            prob_dict_act.values()))
                        self._raw.anon_entropy_actual_max.append(max_entropy(
                            prob_dict_act.values()))
                        self._raw.anon_entropy_norm_actual.append(entropy_normalized(
                            prob_dict_act.values()))
                        # how did entropy do?
                        if route['source_node'] in prob_dict_act.keys():
                            best_prob = sorted(prob_dict_act.values())[-1]
                            diff = best_prob - \
                                prob_dict_act[route['source_node']]
                            self._raw.anon_entropy_actual_best_diff.append(
                                diff)
                            if diff == 0.0:
                                self._raw.anon_entropy_actual_best_hit += 1

                        ranked_set = route['anonymity_set']['ranked_set']
                        top_rank = sorted(ranked_set.keys())[0]
                        self._raw.anon_top_rank_set_size.append(
                            len(ranked_set[top_rank]))
                        self._raw.anon_top_rank.append(top_rank)

                        diff = self._ranked_nodes_diff(
                            ranked_set, route['source_node'])
                        if diff < 0:
                            self._raw.anon_rank_missing_count += 1
                        else:
                            if diff == 0:
                                self._raw.anon_top_rank_correct_count += 1
                            self._raw.anon_rank_diff_actual.append(diff)

    def all_graphs(self, op):
        return [op(g) for config in self._nx_graphs.values() for g in config.values()]

    #@timeit
    def calculate_metrics(self):
        '''
        Calculate the experiment wide metrics
        '''

        # helper function for iterating all graphs
        def per(sel, tot):
            if tot == 0:
                return 0.0
            return sel / float(tot)

        def w(v, s, d=None): return self._wrapper(v, s, d)

        self._raw.avg_degrees = self.all_graphs(lambda g: average_degree(g))

        # Tooooo slow, only do the first graph
        self._raw.avg_diameters = [nx.diameter(self._nx_graphs.values()[0].values()[0])]

        ##################################################################
        self._metrics['graph'] = {}
        self._metrics['graph']['degree_avg'] = w(
            numpy.mean(self._raw.avg_degrees), 'DEG_a')
        self._metrics['graph']['degree_std'] = w(
            numpy.std(self._raw.avg_degrees), 'DEG_s')

        self._metrics['graph']['diameter_avg'] = w(
            numpy.mean(self._raw.avg_diameters), 'DIA_a')
        #self._metrics['graph']['diameter_std'] = w(
        #    numpy.std(self._raw.avg_diameters), 'DIA_s')

        node_counts = self.all_graphs(lambda g: g.number_of_nodes())
        self._metrics['graph']['node_count_avg'] = w(numpy.mean(node_counts), 'N_a')
        self._metrics['graph']['node_count_std'] = w(numpy.std(node_counts), 'N_s')

        edge_counts = self.all_graphs(lambda g: g.number_of_edges())
        self._metrics['graph']['edge_count_avg'] = w(numpy.mean(edge_counts), 'ED_a')
        self._metrics['graph']['edge_count_std'] = w(numpy.std(edge_counts), 'ED_s')

        ##################################################################
        self._metrics['adversary'] = {}
        adv_count, adv_percent = self._get_number_of_adversaries()
        self._metrics['adversary']['count_avg'] = w(numpy.mean(
            adv_count), 'A_a', '(%f%% of all nodes)' % numpy.mean(adv_percent))
        self._metrics['adversary']['count_std'] = w(numpy.std(adv_count), 'A_s')

        self._metrics['adversary']['messages_intercepted'] = w(
            self._raw.message_inter_count, 'MI_c')
        if self._raw.message_inter_count > 0:
            percent = per(self._raw.message_inter_count,
                          self._raw.message_count)
            self._metrics['adversary']['messages_intercepted_percent'] = w(
                percent, 'MI_p', '%f%%' % (percent * 100))

        self._metrics['adversary']['sender_sets_calculable'] = w(
            self._raw.message_inter_pro_count, 'MIC_c')
        if self._raw.message_inter_pro_count > 0:
            percent = per(self._raw.message_inter_pro_count,
                          self._raw.message_inter_count)
            self._metrics['adversary']['sender_sets_calculable_percent_of_intercepted'] = w(
                percent, 'MIC_p', '%f%%' % (percent * 100))
            percent = per(self._raw.message_inter_pro_count,
                          self._raw.message_count)
            self._metrics['adversary']['sender_sets_calculable_percent_of_total'] = w(
                percent, 'MIC_T_p', '%f%%' % (percent * 100))

        ##################################################################
        self._metrics['routing'] = {}
        self._metrics['routing']['message_count'] = w(self._raw.message_count, 'M_c')

        self._metrics['routing']['path_length_routing_avg'] = w(numpy.mean(
            self._raw.routing_path_lengths), 'PR_a')
        self._metrics['routing']['path_length_routing_std'] = w(numpy.std(
            self._raw.routing_path_lengths), 'PR_s')

        self._metrics['routing']['path_length_circuit_avg'] = w(numpy.mean(
            self._raw.circiut_path_lengths), 'PC_a')
        self._metrics['routing']['path_length_circuit_std'] = w(numpy.std(
            self._raw.circiut_path_lengths), 'PC_s')

        ##################################################################
        self._metrics['anonymity'] = {}
        if len(self._raw.sender_set_size) > 0:
            self._metrics['anonymity']['sender_set_size_avg'] = w(
                numpy.mean(self._raw.sender_set_size), 'SS_a')
            self._metrics['anonymity']['sender_set_size_std'] = w(
                numpy.std(self._raw.sender_set_size), 'SS_s')
            self._metrics['anonymity']['entropy_avg'] = w(
                numpy.mean(self._raw.anon_entropy), 'EN_a')
            self._metrics['anonymity']['entropy_std'] = w(
                numpy.std(self._raw.anon_entropy), 'EN_s')
            self._metrics['anonymity']['normalized_entropy_avg'] = w(
                numpy.mean(self._raw.anon_entropy_norm), 'EN_N_s')
            self._metrics['anonymity']['normalized_entropy_std'] = w(
                numpy.std(self._raw.anon_entropy_norm), 'EN_N_s')
            self._metrics['anonymity']['entropy_acutal_dist_avg'] = w(
                numpy.mean(self._raw.anon_entropy_actual), 'EN_A_a')
            self._metrics['anonymity']['entropy_acutal_dist_std'] = w(
                numpy.std(self._raw.anon_entropy_actual), 'EN_A_s')
            self._metrics['anonymity']['normailzed_entropy_acutal_dist_avg'] = w(
                numpy.mean(self._raw.anon_entropy_norm_actual), 'EN_A_N_a')
            self._metrics['anonymity']['normailzed_entropy_acutal_dist_std'] = w(
                numpy.std(self._raw.anon_entropy_norm_actual), 'EN_A_N_s')
            self._metrics['anonymity']['top_rank_set_size_avg'] = w(
                numpy.mean(self._raw.anon_top_rank_set_size), 'TR_S_a')
            self._metrics['anonymity']['top_rank_set_size_std'] = w(
                numpy.std(self._raw.anon_top_rank_set_size), 'TR_S_s')
            self._metrics['anonymity']['top_rank_value_avg'] = w(
                numpy.mean(self._raw.anon_top_rank), 'TR_V_a')
            self._metrics['anonymity']['top_rank_value_std'] = w(
                numpy.std(self._raw.anon_top_rank), 'TR_V_s')

            ##############################################################
            self._metrics['anonymity_accuracy'] = {}
            self._metrics['anonymity_accuracy']['entropy_missed_actual_source'] = w(
                self._raw.anon_entropy_missing_count, 'EN_M_c')
            percent = per(self._raw.anon_entropy_missing_count,
                          self._raw.message_inter_pro_count)
            self._metrics['anonymity_accuracy']['entropy_missed_actual_source_percent'] = w(
                percent, 'EN_M_p', '%f%%' % (percent * 100))

            # entropy
            self._metrics['anonymity_accuracy']['entropy_most_likely_hit'] = w(
                self._raw.anon_entropy_best_hit, 'EN_BH_c')
            percent = per(self._raw.anon_entropy_best_hit,
                          self._raw.message_inter_pro_count)
            self._metrics['anonymity_accuracy']['entropy_most_likely_hit_percent'] = w(
                percent, 'EN_BH_p', '%f%%' % (percent * 100))

            self._metrics['anonymity_accuracy']['entropy_most_likely_diff_hit_avg'] = w(
                numpy.average(self._raw.anon_entropy_best_diff), 'EN_D_a')
            self._metrics['anonymity_accuracy']['entropy_most_likely_diff_hit_std'] = w(
                numpy.std(self._raw.anon_entropy_best_diff), 'EN_D_s')

            # actual entropy
            self._metrics['anonymity_accuracy']['entropy_actual_most_likely_hit'] = w(
                self._raw.anon_entropy_actual_best_hit, 'EN_A_BH_c')
            percent = per(self._raw.anon_entropy_actual_best_hit,
                          self._raw.message_inter_pro_count)
            self._metrics['anonymity_accuracy']['entropy_actual_most_likely_hit_percent'] = w(
                percent, 'EN_A_BH_p', '%f%%' % (percent * 100))

            self._metrics['anonymity_accuracy']['entropy_actual_most_likely_diff_hit_avg'] = w(
                numpy.average(self._raw.anon_entropy_actual_best_diff), 'EN_A_D_a')
            self._metrics['anonymity_accuracy']['entropy_actual_most_likely_diff_hit_std'] = w(
                numpy.std(self._raw.anon_entropy_actual_best_diff), 'EN_A_D_s')

            # ranked
            self._metrics['anonymity_accuracy']['ranked_missed_actual_source'] = w(
                self._raw.anon_rank_missing_count, 'R_M_c')
            percent = per(self._raw.anon_rank_missing_count,
                          self._raw.message_inter_pro_count)
            self._metrics['anonymity_accuracy']['ranked_missed_actual_source_percent'] = w(
                percent, 'R_M_p', '%f%%' % (percent * 100))

            self._metrics['anonymity_accuracy']['rank_diff_from_actual_avg'] = w(
                numpy.mean(self._raw.anon_rank_diff_actual), 'R_D_a')
            self._metrics['anonymity_accuracy']['rank_diff_from_actual_std'] = w(
                numpy.std(self._raw.anon_rank_diff_actual), 'R_D_s')

            self._metrics['anonymity_accuracy']['top_rank_correct'] = w(
                self._raw.anon_top_rank_correct_count, 'TR_H_c')
            percent = per(self._raw.anon_top_rank_correct_count,
                          self._raw.message_inter_pro_count)
            self._metrics['anonymity_accuracy']['top_rank_correct_percent'] = w(
                percent, 'TR_H_p', '%f%%' % (percent * 100))

        ##################################################################
        self._metrics['_raw'] = self._raw.to_dict()

    def get_summary(self):
        '''
        Get the summation metric values
        :return: Dictionary of the metric values
        '''
        return self._metrics

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
        series_list = ['Entropy', 'Max Entropy']

        largest = sorted(self._raw.anon_entropy)[-1]
        step = largest / 20.0
        buckets = [round(i * step, 3) for i in range(0, 21)]

        def _bucket(x):
            for buck in reversed(buckets):
                if round(x, 3) >= buck:
                    return buck
            raise Exception('Something went wrong: bucketing')

        def _labels():
            for buck in buckets:
                yield buck

        labels, entropy_data, start, stop = to_histogram_floats(
            self._raw.anon_entropy, 0.0, largest, _bucket, _labels)
        return {'labels': labels, 'data': entropy_data, 'series': series_list}

    def graph_entropy_normalized(self):
        '''
        Generate a graph histogram of the entropy values by .05
        :return: dict of graph data
        '''
        series_list = ['Entropy']

        largest = 1.0
        step = largest / 20.0
        buckets = [round(i * step, 3) for i in range(0, 21)]

        def _bucket(x):
            for buck in reversed(buckets):
                if round(x, 3) >= buck:
                    return buck
            raise Exception('Something went wrong: bucketing')

        def _labels():
            for buck in buckets:
                yield buck
        labels, data, start, stop = to_histogram_floats(
            self._raw.anon_entropy_norm, 0.0, largest, _bucket, _labels)
        return {'labels': labels, 'data': data, 'series': series_list}

    def graph_entropy_by_hop(self):
        '''
        Generate a graph avg entropy by intercepted at hop
        :return: dict of graph data
        '''
        series_list = ['Entropy Average',
                       'Entropy Standard Deviation',
                       'Max Entropy Average']

        graph = self._graph_by_hop(series_list,
                                   self._raw.adv_inter_hop_calced,
                                   self._raw.anon_entropy)
        graph_max = self._graph_by_hop(series_list,
                                       self._raw.adv_inter_hop_calced,
                                       self._raw.anon_entropy_max)
        graph['data'].append(graph_max['data'][0])
        return graph

    def graph_entropy_normalized_by_hop(self):
        '''
        Generate a graph avg entropy by intercepted at hop
        :return: dict of graph data
        '''
        series_list = ['Entropy Average',
                       'Entropy Standard Deviation']

        return self._graph_by_hop(series_list,
                                  self._raw.adv_inter_hop_calced,
                                  self._raw.anon_entropy_norm)

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

    def graph_entropy_actual(self):
        '''
        Generate a graph histogram of the entropy values by .05
        :return: dict of graph data
        '''
        series_list = ['Entropy']

        largest = sorted(self._raw.anon_entropy_actual)[-1]
        step = largest / 20.0
        buckets = [round(i * step, 3) for i in range(0, 21)]

        def _bucket(x):
            for buck in reversed(buckets):
                if round(x, 3) >= buck:
                    return buck
            raise Exception('Something went wrong: bucketing')

        def _labels():
            for buck in buckets:
                yield buck

        labels, data, start, stop = to_histogram_floats(
            self._raw.anon_entropy_actual, 0.0, 1.0, _bucket, _labels)
        return {'labels': labels, 'data': data, 'series': series_list}

    def graph_entropy_normalized_actual(self):
        '''
        Generate a graph histogram of the entropy values by .05
        :return: dict of graph data
        '''
        series_list = ['Entropy']

        largest = 1.0
        step = largest / 20.0
        buckets = [round(i * step, 3) for i in range(0, 21)]

        def _bucket(x):
            for buck in reversed(buckets):
                if round(x, 3) >= buck:
                    return buck
            raise Exception('Something went wrong: bucketing')

        def _labels():
            for buck in buckets:
                yield buck

        labels, data, start, stop = to_histogram_floats(
            self._raw.anon_entropy_norm_actual, 0.0, 1.0, _bucket, _labels)
        return {'labels': labels, 'data': data, 'series': series_list}

    def graph_entropy_by_hop_actual(self):
        '''
        Generate a graph avg entropy by intercepted at hop
        :return: dict of graph data
        '''
        series_list = ['Entropy Average',
                       'Entropy Standard Deviation',
                       'Max Entropy Average']

        graph = self._graph_by_hop(series_list,
                                   self._raw.adv_inter_hop_calced,
                                   self._raw.anon_entropy_actual)
        graph_max = self._graph_by_hop(series_list,
                                       self._raw.adv_inter_hop_calced,
                                       self._raw.anon_entropy_actual_max)
        graph['data'].append(graph_max['data'][0])
        return graph

    def graph_entropy_normalized_by_hop_actual(self):
        '''
        Generate a graph avg entropy by intercepted at hop
        :return: dict of graph data
        '''
        series_list = ['Entropy Average',
                       'Entropy Standard Deviation']

        return self._graph_by_hop(series_list,
                                  self._raw.adv_inter_hop_calced,
                                  self._raw.anon_entropy_norm_actual)

    def graph_intercept_hop(self):
        '''
        Generate a graph of where adversaries intercepted a message
        :return: dict of graph data
        '''
        series_list = ['Adversary Intercept Hop']
        labels, data, start, stop = to_histogram_ints(
            self._raw.adv_inter_hop, 1)
        return {'labels': labels, 'data': data, 'series': series_list}

    def graph_intercept_percent_hop(self):
        '''
        Generate a graph of where adversaries intercepted a message
        :return: dict of graph data
        '''
        series_list = ['Adversary Intercept Percent by Hop']
        labels, data, start, stop = to_histogram_ints(
            self._raw.adv_inter_hop, 1)
        total = float(sum(data))
        data_per = []
        running_sum = 0.0
        for intered in data:
            running_sum += intered / total
            data_per.append(round(running_sum, 3))
        return {'labels': labels, 'data': [data_per], 'series': series_list}

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

        labels, r_data, start, stop = to_histogram_ints(
            self._raw.routing_path_lengths, 1)
        labels, c_data, start, stop = to_histogram_ints(
            self._raw.circiut_path_lengths, start, stop)

        return {'labels': labels, 'data': [r_data, c_data], 'series': series_list}

    def _wrapper(self, value, short_name, description=None):
        return {'value': value, 'description': description, 'short_name': short_name}

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
        for config, graphs_by_cycle in self._nx_graphs.items():
            for graph in graphs_by_cycle.values():
                count = len(
                    [n for n in graph.node if graph.node[n]['adversary'] == 1])
                adversaries_count.append(count)
                adversaries_percent.append(
                    (count / float(graph.number_of_nodes()) * 100))
        return (adversaries_count, adversaries_percent)

    def _post_process_route_data(self, data, parameters, routing_choice_avg):
        #'''
        # Add the routing data from a single route
        #:param data: dict that contains the experiment route data
        #'''
        current_cycle = data['cycle']
        nx_graph = self._closest_graph(parameters, current_cycle)

        # calculate soure and destination difference
        source_node = nx_graph.node[data['source_node']]
        destination_node = nx_graph.node[data['destination_node']]
        x_loc = source_node['location']
        y_loc = destination_node['location']
        data['distance'] = distance(x_loc, y_loc)

        self._calculate_anonymity_set(
            data, nx_graph, parameters, routing_choice_avg)

    def _calculate_anonymity_set(self, data, nx_graph, parameters, routing_choice_avg):
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
                if int(parameters['look_ahead']) == 1:
                    route_alg = r_tree.rank_greedy
                elif int(parameters['look_ahead']) == 2:
                    route_alg = r_tree.rank_greedy_2_hop
                else:
                    raise Exception('Unknown number of look ahead')
            else:
                raise Exception('Unknown routing type')

            a_data['ranked_set'] = r_tree.get_sender_set_rank(
                route_alg, data['target'])
            a_data['probability_set'] = r_tree.get_sender_set_distribution(
                route_alg, r_tree.distro_rank_exponetial_backoff, data['target'])

            # calculate the probability distribution using the actual routing choices
            largest_rank = sorted(routing_choice_avg.keys())[-1]

            def distro_rank(rank):
                if rank > largest_rank:
                    return (routing_choice_avg[largest_rank] / (2 * (rank - largest_rank))) / 100.0
                return routing_choice_avg[rank] / 100.0
            a_data['probability_set_actual'] = r_tree.get_sender_set_distribution(
                route_alg, distro_rank, data['target'])
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

    def _closest_graph(self, config, cycle):
        config_hash = Configuration.get_hash(config)
        if config_hash not in self._nx_graphs:
            raise Exception('Graph wiht given hash not found')
        keys = self._nx_graphs[config_hash].keys()
        keys.sort()
        previous_key = keys[0]
        for key in keys:
            if key > cycle:
                return self._nx_graphs[config_hash][previous_key]
            previous_key = key
        # return the last one
        return self._nx_graphs[config_hash][keys[-1]]

    def _read_routes(self, routing_data_file_name):
        with open(routing_data_file_name) as r_file:
            for data_line in r_file.readlines():
                yield json.loads(data_line)
