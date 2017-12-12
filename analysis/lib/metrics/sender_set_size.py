# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Calculate the send set for each captured route
'''
import numpy
from lib.metrics.metric_base import MetricBase


class SenderSetSize(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def process(self, data_object):
        '''
        Process a given file
        :param data_object: JSON object
        :return: Updated data_object reference
        '''
        super(SenderSetSize, self).process(data_object)
        if 'anonymity_set' not in data_object or not data_object['anonymity_set']['calculated']:
            return data_object

        self.add_column('sender_set_size')
        self.add_row([int(data_object['anonymity_set']['full_set']['length'])])
        return data_object

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.data_frame

        bins = numpy.arange(0, data_frame.max().max() + 2, dtype=int)
        set_counts, r_bins = numpy.histogram(
            data_frame['sender_set_size'], bins=bins)

        labels = list(bins[:-1])
        series_list = list(data_frame.columns)
        return self._graph_structure(labels, [list(set_counts)],
                                     series_list, 'bar',
                                     'Sender Set Size: Histogram')

    def create_summation(self):
        '''
        Create a list of summation metrics for this data set
        :return: metric list
        '''
        # average up the values based on choice
        data_frame = self.data_frame
        metrics = []
        # average
        mean = float(data_frame['sender_set_size'].mean())
        std = float(data_frame['sender_set_size'].std())
        metrics.append(self._w(round(mean, 5), '',
                               'SS_a', 'sender_set_size_avg'))
        metrics.append(self._w(round(std, 5), '',
                               'SS_s', 'sender_set_size_std'))
        self._replace_nan(metrics)
        return metrics

    def get_count(self):
        '''
        Get number of calculated anonymity sets
        :return: int # of calculated sets
        '''
        return len(self.data_frame)
