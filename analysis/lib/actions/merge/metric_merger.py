# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files
'''
from lib.utils import metric_iter, metric_add, metric_get


class MetricManagerMerger(object):
    '''
    Average a set of repeat experiments
    '''

    def __init__(self):
        self.merged_data = {}
        self.merged_config = {}

    def get_merged_data(self):
        '''
        Get the final merged data of all the Metric managers
        :return: Dict of the merged data
        '''
        return self.merged_data

    def get_merged_config(self):
        '''
        Get the final merged configuration of all the Metric managers
        :return: Dict of the merged data
        '''
        return self.merged_config

    def process(self, data_object):
        '''
        Process a given file
        :param data_object: MetricManager instance
        :return: Updated data_object reference
        '''
        analysis_metrics = data_object.analyze()
        # merge the data sets
        for group_key, metric_key, metric_obj in metric_iter(analysis_metrics):
            existing = metric_get(group_key, metric_key, self.merged_data)
            # new entry?
            if existing is None:
                metric_add(metric_obj, self.merged_data, group_key, metric_key)
                continue
            # merge existing metrics
            existing.merge(metric_obj)
        # merge config
        for config, config_value in data_object.get_config().items():
            # new entry
            if config not in self.merged_config:
                self.merged_config[config] = config_value
                continue
            # merge existing entry, keep common values
            if self.merged_config[config] != config_value:
                self.merged_config[config] = None
        return data_object

    def on_start(self, file_path):
        '''
        Start of processing a new class
        :param file_path: Full path to the class being processed
        '''
        pass

    def on_stop(self):
        '''
        End of processing a new class
        '''
        pass
