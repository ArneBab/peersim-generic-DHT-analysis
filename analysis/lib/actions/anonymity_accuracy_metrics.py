# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Calculate the send set for each captured route
'''
import numpy
from lib.utils import percent
from lib.actions.metric_base import MetricBase


class AnonymityAccuracyMetrics(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def process(self, data_object):
        data_object = super(AnonymityAccuracyMetrics,
                            self).process(data_object)
        # no anonymity set calculated
        if 'anonymity_set' not in data_object or not data_object['anonymity_set']['calculated']:
            return data_object

        self.add_column('entropy_missed')
        self.add_column('best_entropy_diff')
        self.add_column('best_entropy_hit')

        self.add_column('best_entropy_actual_diff')
        self.add_column('best_entropy_actual_hit')

        self.add_column('rank_missed')
        self.add_column('rank_hit_in')
        self.add_column('top_rank_hit')
        self.add_column('top_rank_size')
        self.add_column('hop')

        self.add_column('sender_set_missed')

        row = []
        # exponential backoff entropies
        entropy_set = data_object['anonymity_set']['probability_set']
        entropy_missed = 1
        best_entropy_diff = numpy.nan
        best_entropy_hit = 0
        # entropy did not miss source node
        if data_object['source_node'] in entropy_set.keys():
            entropy_missed = 0
            best_entropy_diff = sorted(
                entropy_set.values())[-1] - entropy_set[data_object['source_node']]
            if best_entropy_diff == 0.0:
                best_entropy_hit = 1
        row.append(entropy_missed)
        row.append(best_entropy_diff)
        row.append(best_entropy_hit)

        # actual backoff probabilities
        entropy_set = data_object['anonymity_set']['probability_set_actual']
        best_entropy_diff = numpy.nan
        best_entropy_hit = 0
        # entropy did not miss source node
        if data_object['source_node'] in entropy_set.keys():
            best_entropy_diff = sorted(
                entropy_set.values())[-1] - entropy_set[data_object['source_node']]
            if best_entropy_diff == 0.0:
                best_entropy_hit = 1
        row.append(best_entropy_diff)
        row.append(best_entropy_hit)

        # top rank
        ranked_set = data_object['anonymity_set']['ranked_set']
        diff = self._ranked_nodes_diff(ranked_set, data_object['source_node'])
        relative_rank_hit_in = self._get_relative_rank_count(
            ranked_set, data_object['source_node'])
        rank_missed = 1
        top_rank_hit = 0
        if diff >= 0:
            rank_missed = 0
        if diff == 0:
            top_rank_hit = 1
        row.append(rank_missed)
        row.append(relative_rank_hit_in)
        row.append(top_rank_hit)

        sorted_rank = sorted(ranked_set.keys())
        top_rank = sorted_rank[0]
        row.append(len(ranked_set[top_rank]))

        row.append(int(data_object['anonymity_set']['hop']))

        sender_set = data_object['anonymity_set']['full_set']['nodes']
        sender_set_missed = 0 if data_object['source_node'] in sender_set else 1
        row.append(sender_set_missed)

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
        if len(data_frame) <= 0:
            return metrics

        # total
        metrics.append(self._w(len(data_frame), '',
                               'EN_T', 'entropy_calculated_count'))

        # miss count
        missed = int(data_frame.entropy_missed.sum())
        missed_percent = percent(missed, int(
            data_frame.entropy_missed.count()))
        metrics.append(self._w(missed, '',
                               'EN_M_c', 'entropy_missed_source_node_count'))
        metrics.append(self._w(round(missed_percent, 5), '',
                               'EN_M_p', 'entropy_missed_source_node_percent'))

        # sender set missed
        missed = int(data_frame.sender_set_missed.sum())
        missed_percent = percent(missed, int(
            data_frame.sender_set_missed.count()))
        metrics.append(self._w(missed, '',
                               'SS_M_c', 'sender_set_missed_count'))
        metrics.append(self._w(round(missed_percent, 5), '',
                               'SS_M_p', 'sender_set_missed_percent'))

        # entropy exponential backoff
        hit = int(data_frame.best_entropy_hit.sum())
        hit_percent = percent(hit, int(data_frame.best_entropy_hit.count()))
        metrics.append(self._w(hit, '',
                               'EN_BH_c', 'best_entropy_hit_count'))
        metrics.append(self._w(round(hit_percent, 5), '',
                               'EN_BH_p', 'best_entropy_hit_percent'))

        metrics.append(self._w(round(data_frame.best_entropy_diff.mean(), 5), '',
                               'EN_D_a', 'best_entropy_diff_avg'))
        metrics.append(self._w(round(data_frame.best_entropy_diff.std(), 5), '',
                               'EN_D_s', 'best_entropy_diff_std'))

        # entropy actual backoff
        hit = int(data_frame.best_entropy_actual_hit.sum())
        hit_percent = percent(
            hit, int(data_frame.best_entropy_actual_hit.count()))
        metrics.append(self._w(hit, '',
                               'EN_A_BH_c', 'best_entropy_actual_hit_count'))
        metrics.append(self._w(round(hit_percent, 5), '',
                               'EN_A_BH_p', 'best_entropy_actual_hit_percent'))

        metrics.append(self._w(round(data_frame.best_entropy_actual_diff.mean(), 5), '',
                               'EN_A_D_a', 'best_entropy_actual_diff_avg'))
        metrics.append(self._w(round(data_frame.best_entropy_actual_diff.std(), 5), '',
                               'EN_A_D_s', 'best_entropy_actual_diff_std'))

        # top rank
        missed = int(data_frame.rank_missed.sum())
        missed_percent = percent(missed, int(data_frame.rank_missed.count()))
        metrics.append(self._w(missed, '',
                               'R_M_c', 'rank_missed_source_node_count'))
        metrics.append(self._w(round(missed_percent, 5), '',
                               'R_M_p', 'rank_missed_source_node_percent'))

        hit = int(data_frame.top_rank_hit.sum())
        hit_percent = percent(hit, int(data_frame.top_rank_hit.count()))
        metrics.append(self._w(hit, '',
                               'TR_H_c', 'top_rank_hit_count'))
        metrics.append(self._w(round(hit_percent, 5), '',
                               'TR_H_p', 'top_rank_hit_percent'))
        metrics.append(self._w(round(data_frame.top_rank_size.mean(), 5), '',
                               'TR_S_a', 'top_rank_size_avg'))
        metrics.append(self._w(round(data_frame.top_rank_size.std(), 5), '',
                               'TR_S_s', 'top_rank_size_std'))
        metrics.append(self._w(round(data_frame.rank_hit_in.mean(), 5), '',
                               'RR_H_a', 'relative_rank_hit_avg'))
        metrics.append(self._w(round(data_frame.rank_hit_in.std(), 5), '',
                               'RR_H_s', 'relative_rank_hit_std'))

        self._replace_nan(metrics)
        return metrics

    def _ranked_nodes_diff(self, ranked_set, source_node_id):
        sorted_rank = sorted(ranked_set.keys())
        top_rank = sorted_rank[0]
        for rank in sorted_rank:
            if source_node_id in ranked_set[rank]:
                return rank - top_rank
        return -1

    def _get_relative_rank_count(self, ranked_set, source_node_id):
        sorted_rank = sorted(ranked_set.keys())
        rank_count = 1
        for rank in sorted_rank:
            if source_node_id in ranked_set[rank]:
                return rank_count
            rank_count += 1
        return 0


class AnonymityHitAtHop(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self, anonymity_accuracy):
        super(AnonymityHitAtHop, self).__init__()
        self.anonymity_accuracy = anonymity_accuracy

    def on_stop(self):
        super(AnonymityHitAtHop, self).on_stop()
        data_frame = self.anonymity_accuracy.data_frame
        if len(data_frame) <= 0:
            return

        data_sum = data_frame.groupby(['hop']).agg(
            {'top_rank_hit': 'sum', 'best_entropy_hit': 'sum', 'best_entropy_actual_hit': 'sum', 'rank_missed': 'count'}).reset_index()
        data_sum.rename(columns={'rank_missed': 'hop_count'}, inplace=True)
        self.data_frame = data_sum

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.data_frame
        if len(data_frame) <= 0:
            return {}

        labels = list(data_frame.hop)
        series_list = ['best entropy hit percent',
                       'best entropy actual hit percent', 'top rank hit percent',
                       'cummulative top rank hit accuracy']

        # calculate cummulative accuracy
        cummulative_data = []
        hit_count = 0
        total_count = 0
        for _, row in data_frame.iterrows():
            hit_count += row.top_rank_hit
            total_count += row.hop_count
            cummulative_data.append(percent(hit_count, total_count))

        # other accuracies
        data = [list(data_frame.best_entropy_hit / data_frame.hop_count),
                list(data_frame.best_entropy_actual_hit / data_frame.hop_count),
                list(data_frame.top_rank_hit / data_frame.hop_count),
                cummulative_data]
        data = self._round(data)

        return self._graph_structure(labels, data,
                                     series_list, 'line',
                                     'Anonymity Metric Accuracy at Intercepted Hop: Percent')


class AnonymityTopRankAccuracyByRank(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self, anonymity_accuracy):
        super(AnonymityTopRankAccuracyByRank, self).__init__()
        self.anonymity_accuracy = anonymity_accuracy

    def on_stop(self):
        super(AnonymityTopRankAccuracyByRank, self).on_stop()
        data_frame = self.anonymity_accuracy.data_frame
        if len(data_frame) <= 0:
            return

        data_frame = data_frame.groupby(['rank_hit_in']).count().reset_index()
        self.data_frame = data_frame

    def create_graph(self):
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
        # sum up the values based on cycle
        data_frame = self.data_frame
        if len(data_frame) <= 0:
            return {}

        labels = list(data_frame.rank_hit_in)
        series_list = ['relative rank hit percent', 'cummulative relative rank hit percent']
        total_count = len(self.anonymity_accuracy.data_frame)
        data_frame = data_frame.apply(lambda c: c / total_count, axis=1)

        # calculate cummulative hits
        cummulative_data = []
        cummulative_hits = 0.0
        for _, row in data_frame.iterrows():
            cummulative_hits += row.hop
            cummulative_data.append(cummulative_hits)

        # other accuracies
        data = [list(data_frame.hop), cummulative_data]
        data = self._round(data)

        return self._graph_structure(labels, data,
                                     series_list, 'line',
                                     'Cummulative Relative Rank Hit Percent')
