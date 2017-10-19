# -*- coding: utf-8 -*-
'''
Updated on October, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Run post processing analysis on data
'''
import os
import json
import pandas
import logging
#import matplotlib.pyplot as plt
import numpy
from scipy import stats
from lib.utils import entropy, entropy_normalized, max_entropy


class PostAnalysis(object):
    '''
    Post analysis operations
    '''

    def __init__(self, data_file_directory):
        self._data_directory = data_file_directory
        self._routing_data_file = os.path.join(
            data_file_directory, 'processed.routing.json')
        self._consolidated_data_file = os.path.join(
            data_file_directory, 'metrics', 'consolidated.json')
        if not os.path.exists(self._routing_data_file):
            raise Exception(
                'Post process unable to find the file %s',
                self._routing_data_file)
        if not os.path.exists(self._consolidated_data_file):
            raise Exception(
                'Post process unable to find the file %s',
                self._consolidated_data_file)

        # read values from consolidated data file
        with(open(self._consolidated_data_file, 'r')) as c_file:
            cons = json.loads(c_file.read())
        self._node_count = cons['graph']['node_count_avg']['value']
        self._degree = cons['graph']['degree_avg']['value']
        self._edge_count = cons['graph']['edge_count_avg']['value']
        self._diameter = cons['graph']['diameter_avg']['value']

    def process_performance(self, performance_csv):
        name_type = 'performance'
        stop_index = -4
        data = pandas.read_csv(performance_csv)
        x = data.iloc[:, 1:stop_index]
        self._corr(x, name_type)    
        self._scatter(x, name_type, 0)

    def process_anonymity(self, performance_csv):
        name_type = 'anonymity'
        stop_index = -4
        data = pandas.read_csv(performance_csv)
        x = data.iloc[:, 1:stop_index]
        self._corr(x, name_type)
        
        # too many variables to do the scatter plot in one go, so break it down
        # circuit_path_length, sender_set_size, entropy_max, adversary_hop
        # circuit_path_length, entropy, entropy_normalized, adversary_hop
        # circuit_path_length, actual_entropy, actual_entropy_normalized, adversary_hop
        # circuit_path_length, entropy_best_diff, actual_entropy_best_diff, adversary_hop
        self._scatter(data.loc[:, ['circuit_path_length', 'sender_set_size', 'entropy_max', 'adversary_hop']], 
                      name_type, 0)
        self._scatter(data.loc[:, ['circuit_path_length', 'entropy', 'entropy_normalized', 'adversary_hop']], 
                      name_type, 1)
        self._scatter(data.loc[:, ['circuit_path_length', 'actual_entropy', 'actual_entropy_normalized', 'adversary_hop']], 
                      name_type, 2)
        self._scatter(data.loc[:, ['circuit_path_length', 'entropy_best_diff', 'actual_entropy_best_diff', 'adversary_hop']], 
                      name_type, 3)
    
    def _scatter(self, data, name_type, count):
        try:
            pandas.plotting.scatter_matrix(data, figsize=(10, 10), diagonal='kde')
            plt.tight_layout()
            plt.savefig(os.path.join(self._data_directory,
                                    'metrics', name_type + '_scatter_' + str(count) + '.png'))
            plt.close('all')
        except Exception:
            # will happen when there is a perfect correlation: eg all 0s
            logging.info('Not writing scatter plot %s', os.path.join(self._data_directory,
                                    'metrics', name_type + '_scatter_' + str(count) + '.png'))
            
    
    def _corr(self, data, name_type):
        corr, pvalues = self._corrcoef_loop(data)
        corr.to_csv(os.path.join(self._data_directory,
                                 'metrics', name_type + '_corr.csv'))
        pvalues.to_csv(os.path.join(self._data_directory,
                                    'metrics', name_type + '_p_values.csv'))

    def _corrcoef_loop(self, matrix):
        rows, cols = matrix.shape[0], matrix.shape[1]
        r_test = pandas.DataFrame(
            index=matrix.columns.values, columns=matrix.columns.values)
        p_value = pandas.DataFrame(
            index=matrix.columns.values, columns=matrix.columns.values)
        for i in range(cols):
            for j in range(i + 1, cols):
                r_, p_ = stats.pearsonr(
                    matrix[matrix.columns[i]], matrix[matrix.columns[j]])
                r_test.at[matrix.columns[i], matrix.columns[j]] = r_
                r_test.at[matrix.columns[j], matrix.columns[i]] = r_
                p_value.at[matrix.columns[i], matrix.columns[j]] = p_
                p_value.at[matrix.columns[j], matrix.columns[i]] = p_
        return r_test, p_value

    def convert_csv_performance(self):
        '''
        Convert routing data to cvs format
        :return: yields list of csv row
        '''
        yield ['id', 'distance', 'routing_path_length', 'circuit_path_length',
               'diameter', 'node_count', 'edge_count', 'degree']
        with(open(self._routing_data_file, 'r')) as r_file:
            for route in r_file:
                yield self._convert_csv_performance(json.loads(route))

    def convert_csv_anonymity(self):
        '''
        Convert routing anonymity data to cvs format
        :return: yields list of csv row
        '''
        yield ['id', 'distance', 'routing_path_length', 'circuit_path_length',
               'sender_set_size', 'entropy_max', 'entropy', 'entropy_normalized',
               'actual_entropy', 'actual_entropy_normalized',
               'entropy_best_diff', 'actual_entropy_best_diff',
               'adversary_hop',
               'diameter', 'node_count', 'edge_count', 'degree']
        with(open(self._routing_data_file, 'r')) as r_file:
            count = 0
            for route in r_file:
                route_json = json.loads(route)
                if 'anonymity_set' not in route_json or not route_json['anonymity_set']['calculated']:
                    continue
                count += 1
                yield self._convert_csv_anonymity(count, route_json)

    def _convert_csv_anonymity(self, id, route):
        prob_dict = route['anonymity_set']['probability_set']
        prob_dict_act = route['anonymity_set']['probability_set_actual']
        source_node = unicode(route['source_node'])

        if source_node not in prob_dict.keys():
            best_diff = 1
        else:
            best_diff = sorted(prob_dict.values())[-1] - \
                prob_dict[source_node]

        if source_node not in prob_dict_act.keys():
            actual_best_diff = 1
        else:
            actual_best_diff = sorted(prob_dict_act.values(
            ))[-1] - prob_dict_act[source_node]

        values = [id, route['distance'],
                  route['routing_path']['length'],
                  route['connection_path']['length'],
                  route['anonymity_set']['full_set']['length'],
                  max_entropy(prob_dict.values()),
                  entropy(prob_dict.values()),
                  entropy_normalized(prob_dict.values()),
                  entropy(prob_dict_act.values()),
                  entropy_normalized(prob_dict_act.values()),
                  best_diff, actual_best_diff,
                  route['anonymity_set']['hop'],
                  self._diameter, self._node_count,
                  self._edge_count, self._degree]
        return [str(value) for value in values]

    def _convert_csv_performance(self, route):
        values = [route['id'], route['distance'],
                  route['routing_path']['length'],
                  route['connection_path']['length'],
                  self._diameter, self._node_count,
                  self._edge_count, self._degree]
        return [str(value) for value in values]
