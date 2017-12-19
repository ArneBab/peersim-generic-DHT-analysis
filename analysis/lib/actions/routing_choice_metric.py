# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files
'''
from lib.actions.metric_base import MetricBase


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
        '''
        Create a graph for the data set
        :return: graph data dict
        '''
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

    def create_summation(self):
        '''
        Create a list of summation metrics for this data set
        :return: metric list
        '''
        # average up the values based on choice
        data_frame = self.data_frame
        # Only choice data
        data_frame = data_frame[data_frame.columns[2:]].fillna(0)
        last_row = data_frame.iloc[len(data_frame) - 1]
        # Calculate average
        metrics = []
        # average
        total = float(last_row.sum())
        for column, data in last_row.items():
            short_name = column.replace('oice ', '_') + '_a'
            metrics.append(self._w(round(data/total, 5), '',
                                   short_name, column.replace(' ', '_') + '_avg'))

        return metrics

    def get_final_routing_choices(self):
        '''
        Create a dict of routing choice to percent choosen
        :return: dict of percents to routing choices
        '''
        data_frame = self.data_frame
        data_frame = data_frame[data_frame.columns[2:]].fillna(0)
        # get the last row
        last_row = data_frame.iloc[len(data_frame) - 1]
        choices = {}
        # average
        total = float(last_row.sum())
        index = 1
        for data in last_row.values:
            choices[index] = data/total
            index += 1
        return choices
