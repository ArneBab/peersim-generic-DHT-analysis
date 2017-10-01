# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Run experiment analysis
'''
import os
import json
import networkx as nx
import numpy

from .configuration import GRAPH_DATA_PATH, Configuration
from .routing_metrics import RoutingMetrics


class Analyzer(object):
    '''
    Class the handles all the experiment analysis
    '''

    _experiment_config_jsons = {}
    _graph_data_directories = {}

    def __init__(self, experiment_config_file_list):
        self._experiment_config_jsons = {}
        self._graph_data_directories = {}
        for experiment_config_file in experiment_config_file_list:
            base_data_directory = os.path.dirname(experiment_config_file)

            with open(experiment_config_file, 'r') as c_file:
                exp_config = json.loads(c_file.read())
            config_hash = Configuration.get_hash(exp_config)
            self._experiment_config_jsons[config_hash] = exp_config
            self._graph_data_directories[config_hash] = os.path.join(
                base_data_directory, GRAPH_DATA_PATH)

    def run_routing_choice_metrics(self):
        '''
        Run analysis of global stats files
        :return: routing choice averages, Graph friendly dict
        '''
        # load the stat files
        stats_data = {}
        largest_choice = 0
        for directory in self._graph_data_directories.values():
            for stat_file_name in self._get_files(directory, '.stats'):
                with open(os.path.join(directory, stat_file_name)) as s_file:
                    data = json.loads(s_file.read())
                    cycle = data['cycle']
                    # skip cycle 0, its empty
                    if cycle == 0:
                        continue
                    for frequency_obj in data['routing_choice_frequency']:
                        choice = frequency_obj['choice']
                        freq = frequency_obj['frequency']

                        if cycle not in stats_data:
                            stats_data[cycle] = {}
                        if choice not in stats_data[cycle]:
                            stats_data[cycle][choice] = 0
                        stats_data[cycle][choice] += freq

                        if choice > largest_choice:
                            largest_choice = choice

        graph_series = ['Choice %d' % i for i in range(1, largest_choice + 1)]
        graph_data = [[] for i in range(0, len(graph_series))]
        label_list = []
        for cycle in sorted(stats_data.keys()):
            choices = stats_data[cycle]
            label_list.append(cycle)
            cycle_total = float(sum(choices.values()))
            for choice in range(1, largest_choice + 1):
                freq = 0
                if choice in choices:
                    freq = choices[choice]
                percent = freq / cycle_total
                graph_data[choice - 1].append(percent)

        routing_choices_average = {}
        for choice_index in range(0, len(graph_data)):
            routing_choices_average[choice_index + 1] = numpy.average(
                graph_data[choice_index])
        return routing_choices_average, self._generate_graph_data(label_list, graph_series, graph_data)

    def get_routing_metrics(self, routing_data_file_name, new_routing_data_file_name, routing_choice_avg):
        '''
        Calculate routing related metrics
        :return: RoutingMetric object
        '''
        return RoutingMetrics(self._load_graphs(), 
                              self._experiment_config_jsons.values(),
                              routing_choice_avg,
                              routing_data_file_name,
                              new_routing_data_file_name)

    def _load_graphs(self):
        graphs = {}
        for config_hash, directory in self._graph_data_directories.items():
            for graph_name in self._get_files(directory, '.gml'):
                graph = nx.read_gml(os.path.join(
                    directory, graph_name), 'id')
                if config_hash not in graphs:
                    graphs[config_hash] = {}
                graphs[config_hash][graph.graph['cycle']] = graph
        return graphs

    def _get_files(self, directory, name_filter):
        return sorted([f for f in os.listdir(directory) if f.endswith(name_filter)])

    def _generate_graph_data(self, label, series_list, data_list):
        return {'labels': label, 'data': data_list, 'series': series_list}
