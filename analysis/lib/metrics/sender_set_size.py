# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Calculate the send set for each captured route
'''
import numpy
from lib.utils import percent
from lib.metrics.metric_base import MetricBase


class SenderSetSize(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self, path_metrics):
        super(SenderSetSize, self).__init__()
        self.path_metrics = path_metrics

    def process(self, data_object):
        '''
        Process a given file
        :param data_object: JSON object
        :return: Updated data_object reference
        '''
        super(SenderSetSize, self).process(data_object)
        self.add_column('sender_set_size')
        self.add_column('intercept_hop')

        # no adversary present
        if 'anonymity_set' not in data_object:
            return data_object

        set_size = numpy.nan
        if data_object['anonymity_set']['calculated']:
            set_size = int(data_object['anonymity_set']['full_set']['length'])
        intercept_hop = int(data_object['anonymity_set']['hop'])

        self.add_row([set_size, intercept_hop])
        return data_object

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.data_frame[self.data_frame.sender_set_size.notnull()]

        bins = numpy.arange(0, data_frame.sender_set_size.max() + 2, dtype=int)
        set_counts, r_bins = numpy.histogram(
            data_frame.sender_set_size, bins=bins)

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

        messages_i = len(data_frame)
        metrics.append(self._w(messages_i, '',
                               'MI_c', 'messages_intercepted'))

        message_total_count = self.path_metrics.get_message_count()
        message_i_percent = percent(messages_i, message_total_count)
        metrics.append(self._w(round(message_i_percent, 5), '',
                               'MI_p', 'messages_intercepted_percent'))

        message_i_c = len(data_frame[data_frame.sender_set_size.notnull()])
        metrics.append(self._w(message_i_c, '',
                               'MIC_c', 'sender_sets_calculable'))

        message_i_c_p = percent(message_i_c, messages_i)
        metrics.append(self._w(round(message_i_c_p, 5), '',
                               'MIC_p', 'sender_sets_calculable_percent_of_intercepted'))

        message_i_c_t_p = percent(message_i_c, message_total_count)
        metrics.append(self._w(round(message_i_c_t_p, 5), '',
                               'MIC_T_p', 'sender_sets_calculable_percent_of_total'))

        metrics.append(self._w(round(data_frame.intercept_hop.mean(), 5), '',
                               'IH_a', 'intercept_hop_avg'))
        metrics.append(self._w(round(data_frame.intercept_hop.std(), 5), '',
                               'IH_s', 'intercept_hop_std'))

        self._replace_nan(metrics)
        return metrics
