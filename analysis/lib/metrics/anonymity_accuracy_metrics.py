# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Calculate the send set for each captured route
'''
import numpy
from lib.utils import percent
from lib.metrics.metric_base import MetricBase


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
        self.add_column('top_rank_hit')

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
        rank_missed = 1
        top_rank_hit = 0
        if diff >= 0:
            rank_missed = 0
        if diff == 0:
            top_rank_hit = 1
        row.append(rank_missed)
        row.append(top_rank_hit)

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

        missed = int(data_frame.entropy_missed.sum())
        missed_percent = percent(missed, int(
            data_frame.entropy_missed.count()))
        metrics.append(self._w(missed, '',
                               'EN_M_c', 'entropy_missed_source_node_count'))
        metrics.append(self._w(round(missed_percent, 5), '',
                               'EN_M_p', 'entropy_missed_source_node_percent'))

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

        self._replace_nan(metrics)
        return metrics

    def _ranked_nodes_diff(self, ranked_set, source_node_id):
        sorted_rank = sorted(ranked_set.keys())
        top_rank = sorted_rank[0]
        for rank in sorted_rank:
            if source_node_id in ranked_set[rank]:
                return rank - top_rank
        return -1