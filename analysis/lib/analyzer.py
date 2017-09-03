# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Run experiment analysis
'''
import os
import json
import networkx as nx

from .configuration import ROUTING_DATA_FILE_NAME, GRAPH_DATA_PATH


class Analyzer(object):
    '''
    Class the handles all the experiment analysis
    '''

    _experiment_config_json = None
    _routing_data_json = {}
    _graph_data_directory = ''
    _graphs = []
    base_data_directory = ''

    def __init__(self, experiment_config_file):
        self.base_data_directory = os.path.dirname(experiment_config_file)
        with open(experiment_config_file, 'r') as c_file:
            self._experiment_config_json = json.loads(c_file.read())
        self._graph_data_directory = os.path.join(
            self.base_data_directory, GRAPH_DATA_PATH)

    # def run(self):
    #    '''
    #    Run the analysis
    #    '''
    #    self._load_routing_data()
    #    self._load_graphs()

    def _load_routing_data(self):
        with open(os.path.join(self.base_data_directory, ROUTING_DATA_FILE_NAME)) as r_file:
            for data_line in r_file.readlines():
                route_data = json.loads(data_line)
                self._routing_data_json[route_data['id']] = route_data

    def run_stats(self):
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
        graph_datasets = []
        # index starts at 1 (sorry :( )
        for i in range(1, len(frequencies.items()) + 1):
            data = []
            # skip first sample (always zeros)
            for j in range(1, len(stats_data_json)):
                if j in frequencies[i]:
                    data.append(frequencies[i][j])
                else:
                    data.append(0)
            graph_datasets.append(
                self._generate_graph_dataset('choice %d' % i, data))
        return self._generate_graph_data(x_label_list[1:], graph_datasets)

    def _load_graphs(self):
        for graph_name in self._get_files(self._graph_data_directory, '.gml'):
            self._graphs.append(nx.read_gml(os.path.join(
                self._graph_data_directory, graph_name)))

    def _get_files(self, directory, name_filter):
        return sorted([f for f in os.listdir(directory) if f.endswith(name_filter)])

    def _generate_graph_data(self, x_label_list, dataset_list):
        return {'labels': x_label_list, 'datasets': dataset_list}

    def _generate_graph_dataset(self, label, data_list):
        return {'label': label, 'data': data_list}
