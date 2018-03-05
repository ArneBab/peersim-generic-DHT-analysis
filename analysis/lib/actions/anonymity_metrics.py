# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Calculate the send set for each captured route
'''
import numpy
from lib.utils import entropy, max_entropy, entropy_normalized, percent
from lib.actions.metric_base import MetricBase


class AnonymityMetrics(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self, graph_manager, path_lengths):
        super(AnonymityMetrics, self).__init__()
        self.graph_manager = graph_manager
        self.path_lengths = path_lengths

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

        self.add_column('entropy_top_rank')
        self.add_column('normalized_entropy_top_rank')

        self.add_column('entropy_sender_set')
        self.add_column('normalized_entropy_sender_set')

        self.add_column('top_rank_set_size')
        self.add_column('hop')

        nx_graph = self.graph_manager.get_graph(data_object['cycle'])
        total_nodes = nx_graph.number_of_nodes()

        row = []
        # exponential backoff entropies
        entropy_set = data_object['anonymity_set']['probability_set']
        row.append(entropy(entropy_set.values()))
        row.append(entropy_normalized(entropy_set.values(), total_nodes))
        row.append(max_entropy(total_nodes))
        # actual backoff entropies
        entropy_set = data_object['anonymity_set']['probability_set_actual']
        row.append(entropy(entropy_set.values()))
        row.append(entropy_normalized(entropy_set.values(), total_nodes))
        # top rank entropies
        entropy_set = data_object['anonymity_set']['probability_set_top_rank']
        row.append(entropy(entropy_set.values()))
        row.append(entropy_normalized(entropy_set.values(), total_nodes))
        # sender set entropies
        entropy_set = data_object['anonymity_set']['probability_set_sender_set']
        row.append(entropy(entropy_set.values()))
        row.append(entropy_normalized(entropy_set.values(), total_nodes))
        # top rank
        ranked_set = data_object['anonymity_set']['ranked_set']
        top_rank = sorted(ranked_set.keys())[0]
        row.append(len(ranked_set[top_rank]))

        row.append(int(data_object['anonymity_set']['hop']))

        self.add_row(row)
        return data_object

    def force_summation(self):
        '''
        Determine if summation must always be run
        :return: True if summation need to be recalculated evey time
        '''
        return True

    def create_summation(self):
        '''
        Create a list of summation metrics for this data set
        :return: metric list
        '''
        # average up the values based on choice
        data_frame = self.data_frame
        metrics = []
        # check if me have data
        if len(data_frame) <= 0:
            return metrics

        message_intercepted = len(data_frame) / float(self.path_lengths.get_message_count())
        weighted_entropy_missed = data_frame.max_entropy.mean() * (1 - message_intercepted)

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

        weighted_entropy = data_frame.entropy_actual.mean() * message_intercepted
        weighted_entropy += weighted_entropy_missed
        metrics.append(self._w(round(weighted_entropy, 5), '',
                               'EN_A_w', 'entropy_actual_weighted_protocol'))

        metrics.append(self._w(round(data_frame.normalized_entropy_actual.mean(), 5), '',
                               'EN_N_A_a', 'normalized_entropy_actual_avg'))
        metrics.append(self._w(round(data_frame.normalized_entropy_actual.std(), 5), '',
                               'EN_N_A_s', 'normalized_entropy_actual_std'))

        # entropy using top rank
        metrics.append(self._w(round(data_frame.entropy_top_rank.mean(), 5), '',
                               'EN_T_a', 'entropy_top_rank_avg'))
        metrics.append(self._w(round(data_frame.entropy_top_rank.std(), 5), '',
                               'EN_T_s', 'entropy_top_rank_std'))

        weighted_entropy = data_frame.entropy_top_rank.mean() * message_intercepted
        weighted_entropy += weighted_entropy_missed
        metrics.append(self._w(round(weighted_entropy, 5), '',
                               'EN_T_w', 'entropy_top_rank_weighted_protocol'))

        metrics.append(self._w(round(data_frame.normalized_entropy_top_rank.mean(), 5), '',
                               'EN_N_T_a', 'normalized_entropy_top_rank_avg'))
        metrics.append(self._w(round(data_frame.normalized_entropy_top_rank.std(), 5), '',
                               'EN_N_T_s', 'normalized_entropy_top_rank_std'))

        weighted_entropy = data_frame.normalized_entropy_top_rank.mean() * message_intercepted
        weighted_entropy += (1 - message_intercepted)
        metrics.append(self._w(round(weighted_entropy, 5), '',
                               'EN_N_T_w', 'normalized_entropy_top_rank_weighted_protocol'))

        # entropy using sender set
        metrics.append(self._w(round(data_frame.entropy_sender_set.mean(), 5), '',
                               'EN_SS_a', 'entropy_sender_set_avg'))
        metrics.append(self._w(round(data_frame.entropy_sender_set.std(), 5), '',
                               'EN_SS_s', 'entropy_sender_set_std'))

        weighted_entropy = data_frame.entropy_sender_set.mean() * message_intercepted
        weighted_entropy += weighted_entropy_missed
        metrics.append(self._w(round(weighted_entropy, 5), '',
                               'EN_SS_w', 'entropy_sender_set_weighted_protocol'))

        metrics.append(self._w(round(data_frame.normalized_entropy_sender_set.mean(), 5), '',
                               'EN_N_SS_a', 'normalized_entropy_sender_set_avg'))
        metrics.append(self._w(round(data_frame.normalized_entropy_sender_set.std(), 5), '',
                               'EN_N_SS_s', 'normalized_entropy_sender_set_std'))

        weighted_entropy = data_frame.normalized_entropy_sender_set.mean() * message_intercepted
        weighted_entropy += (1 - message_intercepted)
        metrics.append(self._w(round(weighted_entropy, 5), '',
                               'EN_N_SS_w', 'normalized_entropy_sender_set_weighted_protocol'))

        # top rank
        metrics.append(self._w(round(data_frame.top_rank_set_size.mean(), 5), '',
                               'TR_S_a', 'top_rank_set_size_avg'))
        metrics.append(self._w(round(data_frame.top_rank_set_size.std(), 5), '',
                               'TR_S_s', 'top_rank_set_size_std'))

        # Percent messages intercepted
        metrics.append(self._w(round(message_intercepted, 5), '',
                               'M_I_p', 'messages_intercepted_per'))

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

    def on_stop(self):
        super(AnonymityEntropy, self).on_stop()
        self.data_frame = self.anonymity_metrics.data_frame

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.data_frame
        if len(data_frame) <= 0:
            return {}
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

    def on_stop(self):
        super(AnonymityEntropyAtHop, self).on_stop()
        self.data_frame = self.anonymity_metrics.data_frame

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.data_frame
        if len(data_frame) <= 0:
            return {}

        data_avg = data_frame.groupby(['hop']).mean().reset_index()
        data_std = data_frame.groupby(['hop']).std().reset_index().fillna(0.0)

        # calculate cummulative entropy
        data_sum = data_frame.groupby(['hop']).agg(
            {self.column_name: 'sum', 'top_rank_set_size': 'count'}).reset_index()
        data_sum.rename(columns={'top_rank_set_size': 'hop_count'}, inplace=True)

        cummulative_data = []
        entropy_sum = 0
        total_count = 0
        for _, row in data_sum.iterrows():
            entropy_sum += row[self.column_name]
            total_count += row.hop_count
            cummulative_data.append(percent(entropy_sum, total_count))

        labels = list(data_avg.hop)
        series_list = ['Entropy Average', 'Entropy Standard Deviation',
                       'Cummulative Entropy Average']
        data = [list(data_avg[self.column_name]),
                list(data_std[self.column_name]),
                cummulative_data]

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
        if len(data_frame) <= 0:
            return {}

        data_avg = data_frame.groupby(['hop']).mean().reset_index()
        data_std = data_frame.groupby(['hop']).std().reset_index().fillna(0.0)

        labels = list(data_avg.hop)
        series_list = ['Average', 'Standard Deviation']
        data = [list(data_avg['top_rank_set_size']),
                list(data_std['top_rank_set_size'])]

        return self._graph_structure(labels, data,
                                     series_list, 'line',
                                     'Top Ranked Sender Set Size at Intercepted Hop: Average')
