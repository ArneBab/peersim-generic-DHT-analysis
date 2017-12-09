# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Manage all of the analysis metrics
'''
import logging
import os
import json

from lib.jsons.routing_choice_reader import RoutingChoiceReader
from lib.file.file_finder import FileFinder
from lib.file.json_file_reader import JSONFileReader
from lib.file.class_loader import ClassLoader


METRIC_FILE_NAME = 'metrics.json'


class MetricManager(object):
    '''
    Manage all of the analysis metrics for a given experiment
    '''

    def __init__(self, base_directory, force_run=False):
        base_directory = os.path.abspath(base_directory)
        if not os.path.exists(base_directory):
            raise Exception('Unable to find the directory: %s' %
                            base_directory)

        self.is_dirty = False
        self.force_run = force_run

        if os.path.isdir(base_directory):
            # only directory was passed in
            self.base_directory = base_directory
            self.metric_file_path = os.path.join(
                base_directory, METRIC_FILE_NAME)
        else:
            # full path to the data file passed in
            self.base_directory = os.path.dirname(base_directory)
            self.metric_file_path = base_directory

        logging.debug('Metric file path: %s', self.metric_file_path)
        logging.debug('Metric file directory: %s', self.base_directory)

        # load the metrics file if it exists
        self.metrics = {'graphs': {}, 'data': {}}
        if os.path.exists(self.metric_file_path):
            logging.debug('Loading an existing metric file')
            with open(self.metric_file_path, 'r') as metric_file:
                self.metrics = json.loads(metric_file.read())

    def save_data(self):
        '''
        Save the state of the metrics analysis to a file
        '''
        if not self.is_dirty:
            logging.debug('No changes detected, not writing file')
            return

        with open(self.metric_file_path, 'w') as metric_file:
            logging.debug('Writing metric data to file')
            metric_file.write(json.dumps(self.metrics))

    def archive_data(self):
        '''
        Archive (deflate) the experiment data in this directory.
        Leave the calculated metric data inflated.
        '''
        pass

    def analyze(self):
        '''
        Run experiment analysis
        :return: dict of the metric objects
        '''
        analysis_metrics = {}
        analysis_metrics.update(self._routing_choice())

        return analysis_metrics

    def summarize(self):
        '''
        Run the summation metrics over a set of experiment repeats
        '''
        # check if the summation needs to run

        # load the metric data for each experiment repeat
        metric_managers = ClassLoader(MetricManager)
        finder = FileFinder([metric_managers])
        finder.process(self.base_directory, METRIC_FILE_NAME)
        # merge the repeat data into this metric instance
        merged_state = None
        for metric in metric_managers.class_instance:
            merged_state = self._merge(merged_state, metric)
        # calculate the new data
        for group_name, group_obj in merged_state.items():
            for metric_name, metric_obj in group_obj.items():
                self._set_data(group_name, metric_name, metric_obj.to_csv())
        return self.analyze()

    def _routing_choice(self):
        group_name = 'routing'
        metric_name = 'routing_choice'
        # check if we already have the data
        if self._have_metric_data(group_name, metric_name):
            logging.debug('Loading existing routing choice metric data')
            routing_choice_reader = RoutingChoiceReader.load(
                self._get_data(group_name, metric_name))
            # check if we have graph data
            if self._get_graph(group_name, metric_name) is None:
                logging.debug(
                    'Generating missing graph data: existing data was found')
                self._set_graph(group_name, metric_name,
                                routing_choice_reader.create_graph())
            return {group_name: {metric_name: routing_choice_reader}}

        # no existing data found, recalculate it
        routing_choice_reader = RoutingChoiceReader()
        file_reader = JSONFileReader([routing_choice_reader])
        finder = FileFinder([file_reader])
        finder.process(os.path.join(self.base_directory, 'graphs'), '*.stats')
        self._set_data(group_name, metric_name, routing_choice_reader.to_csv())
        self._set_graph(group_name, metric_name,
                        routing_choice_reader.create_graph())
        return {group_name: {metric_name: routing_choice_reader}}

    def _merge(self, merged_state, other_metric_manager):
        analysis_metrics = other_metric_manager.analyze()
        if merged_state is None:
            return analysis_metrics
        # merge the data sets
        for group_key, group_metrics in analysis_metrics.items():
            for metric_key, metric_obj in group_metrics.items():
                if group_key not in merged_state:
                    merged_state[group_key] = {}
                # if the metric already exists
                if metric_key not in merged_state[group_key]:
                    merged_state[group_key][metric_key] = metric_obj
                    continue
                # merge existing metrics
                merged_state[group_key][metric_key].merge(metric_obj)
        return merged_state

    def _have_metric_data(self, group_name, metric_name):
        return self._get_data(group_name, metric_name) is not None and \
            not self.force_run

    def _get_data(self, group_name, metric_name):
        if group_name in self.metrics['data'] and metric_name in self.metrics['data'][group_name]:
            return self.metrics['data'][group_name][metric_name]
        return None

    def _set_data(self, group_name, metric_name, value):
        self.is_dirty = True
        if group_name not in self.metrics['data']:
            self.metrics['data'][group_name] = {}
        self.metrics['data'][group_name][metric_name] = value

    def _get_graph(self, group_name, metric_name):
        if group_name in self.metrics['graphs'] and \
           metric_name in self.metrics['graphs'][group_name]:
            return self.metrics['graphs'][group_name][metric_name]
        return None

    def _set_graph(self, group_name, metric_name, value):
        self.is_dirty = True
        if group_name not in self.metrics['graphs']:
            self.metrics['graphs'][group_name] = {}
        self.metrics['graphs'][group_name][metric_name] = value
