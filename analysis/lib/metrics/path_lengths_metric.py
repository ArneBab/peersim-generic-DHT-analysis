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
