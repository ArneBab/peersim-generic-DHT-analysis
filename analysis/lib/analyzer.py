# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Run experiment analysis
'''
import os
import json
import networkx as nx

from .configuration import GRAPH_DATA_PATH
from .routingMetrics import RoutingMetrics


class Analyzer(object):
    '''
    Class the handles all the experiment analysis
    '''

    _experiment_config_json = None
    _graph_data_directory = ''
    base_data_directory = ''

    def __init__(self, experiment_config_file):
        self.base_data_directory = os.path.dirname(experiment_config_file)
        with open(experiment_config_file, 'r') as c_file:
            self._experiment_config_json = json.loads(c_file.read())
        self._graph_data_directory = os.path.join(
            self.base_data_directory, GRAPH_DATA_PATH)

    def run_routing_choice_metrics(self):
        '''
        Run analysis of global stats files
        :return: Graph friendly dict
        '''
        # load the stat files
        stats_data_json = []
        for stat_file_name in self._get_files(self._graph_data_directory, '.stats'):
            with open(os.path.join(self._graph_data_directory, stat_file_name)) as s_file:
                stats_data_json.append(json.loads(s_file.read()))
        # sort the stat data
        stats_data_json.sort(key=lambda x: x['cycle'])

        # collect all the values across the experiments
        frequencies = {}
        x_label_list = []
        for i in range(0, len(stats_data_json)):
            sample_total = 0
            stat_entry = stats_data_json[i]
            x_label_list.append(stat_entry['cycle'])
            # count total choices the first pass
            for freq in stat_entry['routing_choice_frequency']:
                sample_total = sample_total + freq['frequency']

            # calculate the percentages
            for freq in stat_entry['routing_choice_frequency']:
                choice = freq['choice']
                if choice not in frequencies:  # add list is not present
                    frequencies[choice] = {}
                if freq['frequency'] == 0:
                    frequencies[choice][i] = 0
                else:
                    frequencies[choice][i] = freq['frequency'] / \
                        float(sample_total) * 100.0

        # convert to graph format and save to file
        graph_data = []
        graph_series = []
        # index starts at 1 (sorry :( )
        for i in range(1, len(frequencies.items()) + 1):
            data = []
            # skip first sample (always zeros)
            for j in range(1, len(stats_data_json)):
                if j in frequencies[i]:
                    data.append(frequencies[i][j])
                else:
                    data.append(0)
            graph_series.append('choice %d' % i)
            graph_data.append(data)
        return self._generate_graph_data(x_label_list[1:], graph_series, graph_data)

    def get_routing_metrics(self, routing_data_file_name):
        '''
        Calculate routing related metrics
        :return: RoutingMetric object
        '''
        return RoutingMetrics(self._load_graphs(), routing_data_file_name)

    def _load_graphs(self):
        graphs = {}
        for graph_name in self._get_files(self._graph_data_directory, '.gml'):
            graph = nx.read_gml(os.path.join(
                self._graph_data_directory, graph_name), 'id')
            graphs[graph.graph['cycle']] = graph
        return graphs

    def _get_files(self, directory, name_filter):
        return sorted([f for f in os.listdir(directory) if f.endswith(name_filter)])

    def _generate_graph_data(self, label, series_list, data_list):
        return {'labels': label, 'data': data_list, 'series': series_list}
