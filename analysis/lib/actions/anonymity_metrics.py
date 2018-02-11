# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Calculate the send set for each captured route
'''
import numpy
from lib.utils import entropy, max_entropy, entropy_normalized
from lib.actions.metric_base import MetricBase


class AnonymityMetrics(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def process(self, data_object):
        data_object = super(AnonymityMetrics, self).process(data_object)
        # no anonymity set calculated
        if 'anonymity_set' not in data_object or not data_object['anonymity_set']['calculated']:
            return data_object

        self.add_column('entropy')
        self.add_column('normalized_entropy')
        self.add_column('max_entropy')

        self.add_column('entropy_actual')
        self.add_column('normalized_entropy_actual')
        self.add_column('max_entropy_actual')

        self.add_column('top_rank_set_size')
        self.add_column('hop')

        row = []
        # exponential backoff entropies
        entropy_set = data_object['anonymity_set']['probability_set']
        row.append(entropy(entropy_set.values()))
        row.append(entropy_normalized(entropy_set.values()))
        row.append(max_entropy(entropy_set.values()))
        # actual backoff entropies
        entropy_set = data_object['anonymity_set']['probability_set_actual']
        row.append(entropy(entropy_set.values()))
        row.append(entropy_normalized(entropy_set.values()))
        row.append(max_entropy(entropy_set.values()))
        # top rank
        ranked_set = data_object['anonymity_set']['ranked_set']
        top_rank = sorted(ranked_set.keys())[0]
        row.append(len(ranked_set[top_rank]))

        row.append(int(data_object['anonymity_set']['hop']))

        self.add_row(row)
        return data_object

    def create_summation(self):
        '''
        Create a list of summation metrics for this data set
        :return: metric list
        '''
        # average up the values based on choice
        data_frame = self.data_frame
        metrics = []
        # entropy exponential backoff
        metrics.append(self._w(round(data_frame.entropy.mean(), 5), '',
                               'EN_a', 'entropy_avg'))
        metrics.append(self._w(round(data_frame.entropy.std(), 5), '',
                               'EN_s', 'entropy_std'))

        metrics.append(self._w(round(data_frame.normalized_entropy.mean(), 5), '',
                               'EN_N_a', 'normalized_entropy_avg'))
        metrics.append(self._w(round(data_frame.normalized_entropy.std(), 5), '',
                               'EN_N_s', 'normalized_entropy_std'))

        metrics.append(self._w(round(data_frame.max_entropy.mean(), 5), '',
                               'EN_M_a', 'max_entropy_avg'))
        metrics.append(self._w(round(data_frame.max_entropy.std(), 5), '',
                               'EN_M_s', 'max_entropy_std'))

        # entropy using actual backoffs
        metrics.append(self._w(round(data_frame.entropy_actual.mean(), 5), '',
                               'EN_A_a', 'entropy_actual_avg'))
        metrics.append(self._w(round(data_frame.entropy_actual.std(), 5), '',
                               'EN_A_s', 'entropy_actual_std'))

        metrics.append(self._w(round(data_frame.normalized_entropy_actual.mean(), 5), '',
                               'EN_N_A_a', 'normalized_entropy_actual_avg'))
        metrics.append(self._w(round(data_frame.normalized_entropy_actual.std(), 5), '',
                               'EN_N_A_s', 'normalized_entropy_actual_std'))

        metrics.append(self._w(round(data_frame.max_entropy_actual.mean(), 5), '',
                               'EN_M_A_a', 'max_entropy_actual_avg'))
        metrics.append(self._w(round(data_frame.max_entropy_actual.std(), 5), '',
                               'EN_M_A_s', 'max_entropy_actual_std'))

        # top rank
        metrics.append(self._w(round(data_frame.top_rank_set_size.mean(), 5), '',
                               'TR_S_a', 'top_rank_set_size_avg'))
        metrics.append(self._w(round(data_frame.top_rank_set_size.std(), 5), '',
                               'TR_S_s', 'top_rank_set_size_std'))

        self._replace_nan(metrics)
        return metrics


class AnonymityEntropy(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self, anonymity_metrics, column_name, graph_name):
        super(AnonymityEntropy, self).__init__()
        self.anonymity_metrics = anonymity_metrics
        self.column_name = column_name
        self.graph_name = graph_name

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.anonymity_metrics.data_frame
        set_counts, r_bins = numpy.histogram(
            data_frame[self.column_name], bins=20)

        labels = [round(r_bin, 3) for r_bin in r_bins]
        series_list = [self.column_name]
        return self._graph_structure(labels, [list(set_counts)],
                                     series_list, 'bar',
                                     self.graph_name + ': Histogram')


class AnonymityEntropyAtHop(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self, anonymity_metrics, column_name, max_column_name, graph_name):
        super(AnonymityEntropyAtHop, self).__init__()
        self.anonymity_metrics = anonymity_metrics
        self.column_name = column_name
        self.max_column_name = max_column_name
        self.graph_name = graph_name

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.anonymity_metrics.data_frame

        data_avg = data_frame.groupby(['hop']).mean().reset_index()
        data_std = data_frame.groupby(['hop']).std().reset_index().fillna(0.0)

        labels = list(data_avg.hop)
        series_list = ['Entropy Average', 'Entropy Standard Deviation']
        data = [list(data_avg[self.column_name]),
                list(data_std[self.column_name])]

        if self.max_column_name:
            series_list.insert(0, 'Max Entropy Average')
            data.insert(0, list(data_avg[self.max_column_name]))

        return self._graph_structure(labels, data,
                                     series_list, 'line',
                                     self.graph_name + ' at Intercepted Hop: Average')


class AnonymityTopRankedSetSize(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self, anonymity_metrics):
        super(AnonymityTopRankedSetSize, self).__init__()
        self.anonymity_metrics = anonymity_metrics

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.anonymity_metrics.data_frame

        data_avg = data_frame.groupby(['hop']).mean().reset_index()
        data_std = data_frame.groupby(['hop']).std().reset_index().fillna(0.0)

        labels = list(data_avg.hop)
        series_list = ['Average', 'Standard Deviation']
        data = [list(data_avg['top_rank_set_size']),
                list(data_std['top_rank_set_size'])]

        return self._graph_structure(labels, data,
                                     series_list, 'line',
                                     'Top Ranked Sender Set Size at Intercepted Hop: Average')