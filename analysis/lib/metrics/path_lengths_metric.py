# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files
'''
import numpy
from lib.metrics.metric_base import MetricBase


class PathLengthsMetric(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def process(self, data_object):
        '''
        Process a given file
        :param data_object: JSON object
        :return: Updated data_object reference
        '''
        super(PathLengthsMetric, self).process(data_object)
        self.add_column('Routing Path Length')
        self.add_column('Circuit Path Length')

        routing_path = data_object['routing_path']['length']
        circuit_path = data_object['connection_path']['length']
        # Add row
        self.add_row([routing_path, circuit_path])
        return data_object

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.data_frame

        bins = numpy.arange(0, data_frame.max().max() + 2, dtype=int)
        route_counts, r_bins = numpy.histogram(
            data_frame['Routing Path Length'], bins=bins)
        circuit_counts, r_bins = numpy.histogram(
            data_frame['Circuit Path Length'], bins=bins)

        labels = list(bins[:-1])
        series_list = list(data_frame.columns)
        return self._graph_structure(labels, [list(route_counts), list(circuit_counts)],
                                     series_list, 'line',
                                     'Path Lengths (Hops): Histogram')

    def create_summation(self):
        '''
        Create a list of summation metrics for this data set
        :return: metric list
        '''
        # average up the values based on choice
        data_frame = self.data_frame
        metrics = []
        # average
        route_values = list(data_frame['Routing Path Length'].values)
        circuit_values = list(data_frame['Circuit Path Length'].values)
        metrics.append(self._value_wrapper(len(route_values), '',
                                           'M_c', 'message_count'))
        metrics.append(self._value_wrapper(round(numpy.mean(route_values), 5), '',
                                           'PR_a', 'path_length_routing_avg'))
        metrics.append(self._value_wrapper(round(numpy.std(route_values), 5), '',
                                           'PR_s', 'path_length_routing_std'))
        metrics.append(self._value_wrapper(round(numpy.mean(circuit_values), 5), '',
                                           'PC_a', 'path_length_circuit_avg'))
        metrics.append(self._value_wrapper(round(numpy.std(circuit_values), 5), '',
                                           'PC_s', 'path_length_circuit_std'))
        return metrics
