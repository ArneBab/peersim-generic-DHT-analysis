# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Calculate the send set for each captured route
'''
import numpy
from lib.actions.metric_base import MetricBase


class AdversaryInterceptHop(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self, sender_set_size):
        super(AdversaryInterceptHop, self).__init__()
        self.sender_set_size = sender_set_size

    def on_stop(self):
        super(AdversaryInterceptHop, self).on_stop()
        self.data_frame = self.sender_set_size.data_frame

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.data_frame

        bins = numpy.arange(0, data_frame.intercept_hop.max() + 2, dtype=int)
        set_counts, _ = numpy.histogram(
            data_frame.intercept_hop, bins=bins)

        labels = list(bins[:-1])
        series_list = list(data_frame.columns)
        return self._graph_structure(labels, [list(set_counts)],
                                     series_list, 'line',
                                     'Aversary Intercept Hop: Histogram')


class AdversaryInterceptHopCalculated(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self, sender_set_size):
        super(AdversaryInterceptHopCalculated, self).__init__()
        self.sender_set_size = sender_set_size

    def on_stop(self):
        super(AdversaryInterceptHopCalculated, self).on_stop()
        self.data_frame = self.sender_set_size.data_frame

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.data_frame

        # only get calculated sender sets
        data_frame = data_frame[data_frame.sender_set_size.notnull()]

        bins = numpy.arange(0, data_frame.intercept_hop.max() + 2, dtype=int)
        set_counts, _ = numpy.histogram(
            data_frame.intercept_hop, bins=bins)

        labels = list(bins[:-1])
        series_list = list(data_frame.columns)
        return self._graph_structure(labels, [list(set_counts)],
                                     series_list, 'line',
                                     'Adversary Intercept Hop (Calculated): Histogram')
