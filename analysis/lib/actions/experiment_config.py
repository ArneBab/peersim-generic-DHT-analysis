# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files
'''
from lib.actions.metric_base import MetricBase
from lib.configuration import Configuration


class ExperimentConfig(MetricBase):
    '''
    Generic interface for JSON based actions
    '''
    def __init__(self):
        super(ExperimentConfig, self).__init__()
        self.config = None

    def process(self, data_object):
        '''
        Process a given file
        :param data_object: JSON object
        :return: Updated data_object reference
        '''
        super(ExperimentConfig, self).process(data_object)
        self.config = data_object
        row = []
        for param in Configuration.get_parameters():
            if param == 'repeat':
                continue
            if param in data_object:
                self.add_column(param)
                row.append(data_object[param])

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
        data_frame = self.data_frame.iloc[0]
        metrics = []
        for column in data_frame.keys():
            metrics.append(self._w(str(data_frame[column]), '', column, column))

        return metrics

    def get_parameter(self, key):
        '''
        Get the experiment configuration value for the given key
        :param key: parameter index name
        :return: value of the parameter
        '''
        return self.data_frame.iloc[len(self.data_frame) - 1][key]

    def get_raw_config(self):
        '''
        Get the raw experiment configuration object
        :param key: parameter index name
        :return: return dict of config settings
        '''
        return self.config
