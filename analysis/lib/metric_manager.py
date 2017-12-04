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
from lib.file.file_reader import FileReader


class MetricManager(object):
    '''
    Manage all of the analysis metrics for a given experiment
    '''

    def __init__(self, base_directory, force_run=False):
        if not os.path.exists(base_directory):
            raise Exception('Unable to find the directory %s' % base_directory)

        self.is_dirty = False
        self.force_run = force_run
        self.base_directory = base_directory
        self.metric_file_path = os.path.join(os.path.abspath(base_directory), 'metrics.json')
        logging.debug('Metric file path: %s', self.metric_file_path)

        # load the metrics file if it exists
        self.metrics = {'graphs':{}, 'data':{}}
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
        '''
        routing_choice = self._routing_choice()

    def _routing_choice(self):
        metric_name = 'routing_choice'
        # check if we already have the data
        if self._have_metric_data(metric_name):
            logging.debug('Loading existing routing choice metric data')
            return RoutingChoiceReader.load(self._get_data(metric_name))

        routing_choice_reader = RoutingChoiceReader()
        file_reader = FileReader([routing_choice_reader])
        file_finder = FileFinder([file_reader])
        file_finder.process(self.base_directory, '/graphs/*.stats')
        self._set_data(metric_name, routing_choice_reader.to_csv())
        self._set_graph(metric_name, routing_choice_reader.create_graph())
        return routing_choice_reader

    def _have_metric_data(self, metric_name):
        return self._get_data(metric_name) is not None and \
               self._get_graph(metric_name) is not None and \
               not self.force_run

    def _get_data(self, metric_name):
        if metric_name in self.metrics['data']:
            return self.metrics['data'][metric_name]
        return None

    def _set_data(self, metric_name, value):
        self.is_dirty = True
        self.metrics['data'][metric_name] = value

    def _get_graph(self, metric_name):
        if metric_name in self.metrics['graphs']:
            return self.metrics['graphs'][metric_name]
        return None

    def _set_graph(self, metric_name, value):
        self.is_dirty = True
        self.metrics['graphs'][metric_name] = value
