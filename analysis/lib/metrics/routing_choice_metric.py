# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files
'''
from lib.metrics.metric_base import MetricBase


class RoutingChoiceMetric(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def process(self, data_object):
        '''
        Process a given file
        :param data_object: Data object
        :return: Updated data_object reference
        '''
        data_object = super(RoutingChoiceMetric, self).process(data_object)

        cycle = data_object['cycle']
        # skip cycle 0, its empty
        if cycle == 0:
            return

        churn = data_object['churn_count']

        frequencies = {}
        for freq_obj in data_object['routing_choice_frequency']:
            frequencies[freq_obj['choice']] = freq_obj['frequency']

        # Add columns and build row data
        row = [cycle, churn]
        self.add_column('cycle')
        self.add_column('churn')
        for i in sorted(frequencies.keys()):
            self.add_column('Choice %d' % i)
            row.append(frequencies[i])

        # Add row
        self.add_row(row)
        return data_object

    def merge(self, other):
        super(RoutingChoiceMetric, self).merge(other)
        # groupby cycle
        self.data_frame = self.data_frame.groupby(
            ['cycle']).sum().reset_index()

    def create_graph(self):
        # sum up the values based on cycle
        data_frame = self.data_frame

        labels = list(data_frame['cycle'])
        # Only choice data
        data_frame = data_frame[data_frame.columns[2:]].fillna(0)
        series_list = list(data_frame.columns)
        # Calculate percent
        data_frame = data_frame.apply(lambda c: c / c.sum(), axis=1)
        data_list = [list(data_frame[column]) for column in data_frame.columns]
        data_list = self._round(data_list)
        return self._graph_structure(labels, data_list, series_list, 'line',
                                     'Routing Preferences Taken: Stacked', True)
