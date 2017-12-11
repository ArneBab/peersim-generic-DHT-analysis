# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files
'''
from lib.metrics.metric_base import MetricBase
from lib.configuration import Configuration


class ExperimentConfig(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def process(self, data_object):
        '''
        Process a given file
        :param data_object: JSON object
        :return: Updated data_object reference
        '''
        super(ExperimentConfig, self).process(data_object)
        row = []
        for param in Configuration.get_parameters():
            if param == 'repeat':
                continue
            if param in data_object:
                self.add_column(param)
                row.append(data_object[param])

        self.add_row(row)
        return data_object

    def create_summation(self):
        '''
        Create a list of summation metrics for this data set
        :return: metric list
        '''
        data_frame = self.data_frame.iloc[0]
        metrics = []
        for column in data_frame.keys():
            metrics.append(self._w(str(data_frame[column]), '', column, column))
        return metrics
