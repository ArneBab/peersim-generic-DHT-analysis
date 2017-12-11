# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files
'''
import math
import networkx as nx
import numpy
from lib.metrics.metric_base import MetricBase


class GraphManager(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def process(self, data_object):
        '''
        Process a given file
        :param data_object: Data object
        :return: Updated data_object reference
        '''
        data_object = super(GraphManager, self).process(data_object)

        # hack!!!! Currently all graphs are static
        # So just read the first graph in the experiment and skip the rest
        # to save on processing time
        if len(self.data_frame) + len(self._rows_to_add) > 0:
            return data_object

        graph = nx.read_gml(data_object, 'id')

        self.add_column('cycle')
        self.add_column('file_path')
        self.add_column('degree_avg')
        self.add_column('degree_std')
        self.add_column('diameter')
        self.add_column('node_count')
        self.add_column('edge_count')

        row = []
        row.append(graph.graph['cycle'])
        row.append(data_object)
        degrees = dict(graph.degree()).values()
        row.append(numpy.mean(degrees))
        row.append(numpy.std(degrees))
        row.append(nx.diameter(graph))
        row.append(graph.number_of_nodes())
        row.append(graph.number_of_edges())

        self.add_row(row)
        return data_object

    def create_summation(self):
        '''
        Create a list of summation metrics for this data set
        :return: metric list
        '''
        # average up the values based on choice
        d_f = self.data_frame
        metrics = []
        metrics.append(self._w(round(d_f['degree_avg'].mean(), 5), '',
                               'DEG_a', 'degree_avg'))
        # average of degree std
        metrics.append(self._w(round(d_f['degree_std'].mean(), 5), '',
                               'DEG_s', 'degree_std'))

        metrics.append(self._w(round(d_f['diameter'].mean(), 5), '',
                               'DIA_a', 'diameter_avg'))
        metrics.append(self._w(round(d_f['diameter'].std(), 5), '',
                               'DIA_s', 'diameter_std'))

        metrics.append(self._w(round(d_f['node_count'].mean(), 5), '',
                               'N_a', 'node_count_avg'))
        metrics.append(self._w(round(d_f['node_count'].std(), 5), '',
                               'N_s', 'node_count_std'))

        metrics.append(self._w(round(d_f['edge_count'].mean(), 5), '',
                               'ED_a', 'edge_count_avg'))
        metrics.append(self._w(round(d_f['edge_count'].std(), 5), '',
                               'ED_s', 'edge_count_std'))

        for metric in metrics:
            if math.isnan(metric['value']):
                metric['value'] = 0.0

        return metrics
