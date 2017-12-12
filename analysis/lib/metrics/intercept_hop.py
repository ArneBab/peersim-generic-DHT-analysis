# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Calculate the send set for each captured route
'''
import numpy
from lib.metrics.metric_base import MetricBase


class InterceptHop(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self, sender_set_size):
        super(InterceptHop, self).__init__()
        self.sender_set_size = sender_set_size

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.sender_set_size.data_frame

        bins = numpy.arange(0, data_frame.intercept_hop.max() + 2, dtype=int)
        set_counts, r_bins = numpy.histogram(
            data_frame.intercept_hop, bins=bins)

        labels = list(bins[:-1])
        series_list = list(data_frame.columns)
        return self._graph_structure(labels, [list(set_counts)],
                                     series_list, 'line',
                                     'Aversary Intercept Hop: Histogram')
