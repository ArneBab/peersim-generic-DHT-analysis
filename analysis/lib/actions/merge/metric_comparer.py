# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files
'''
import math
from lib.actions.metric_base import MetricBase
from lib.configuration import Configuration
from lib.utils import metric_iter, metric_add, metric_get


class MetricManagerComparer(MetricBase):
    '''
    Compare metric managers summation data
    '''

    def __init__(self, experiment_variable):
        super(MetricManagerComparer, self).__init__()
        self.metric_map = {}
        self.experiment_variable = experiment_variable

    def process(self, data_object):
        '''
        Process a given file
        :param data_object: MetricManager instance
        :return: Updated data_object reference
        '''
        self.add_column('experiment_name')
        # ensure we have all the data
        data_object.analyze()
        # check columns first
        for group_key, metric_key, metric_obj in metric_iter(data_object.metrics['summations']):
            for metric in metric_obj:
                metric_name = metric['full_name']
                exists = metric_get(group_key, metric_name, self.metric_map)
                # adding new column
                if exists is None:
                    self.add_column(metric_name)
                    position = len(self.data_frame.columns) + \
                        len(self._columns_to_add) - 1
                    metric_add(position, self.metric_map,
                               group_key, metric_name)
        # populate the values for the table row
        row = [None for pos in range(
            0, len(self.data_frame.columns) + len(self._columns_to_add))]
        row[0] = Configuration.get_hash_name(
            data_object.get_config(), [self.experiment_variable, 'repeat'])

        for group_key, metric_key, metric_obj in metric_iter(data_object.metrics['summations']):
            for metric in metric_obj:
                metric_name = metric['full_name']
                position = metric_get(group_key, metric_name, self.metric_map)
                if position is None:
                    raise Exception('Something very bad happened')
                row[position] = metric['value']
        self.add_row(row)
        return data_object


class SummationVariableComparer(MetricBase):
    '''
    Compare metric managers summation data
    '''

    def __init__(self, metric_comparer, metric_name):
        super(SummationVariableComparer, self).__init__()
        self.metric_comparer = metric_comparer
        self.metric_name = metric_name

    def process(self, data_object):
        '''
        Process a given file
        :param data_object: MetricManager instance
        :return: Updated data_object reference
        '''
        self.data_frame = self.metric_comparer.data_frame[[
            'experiment_name', self.metric_comparer.experiment_variable, self.metric_name]]
        self.data_frame = self.data_frame.pivot(
            index='experiment_name', columns=self.metric_comparer.experiment_variable)

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.data_frame

        labels = [str(sub_col) for col, sub_col in data_frame.columns]
        series_list = []
        datas = []
        for index, row in data_frame.iterrows():
            series_list.append(str(row.name))
            data = []
            for col_name, sub_col_name in data_frame.columns:
                data_value = float(row[col_name][sub_col_name])
                # check for NaN
                if math.isnan(data_value):
                    data_value = 0.0

                data.append(data_value)
            datas.append(data)
        return self._graph_structure(labels, datas,
                                     series_list, 'line',
                                     self.metric_name)
