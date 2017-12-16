# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Manage all of the analysis metrics
'''
import logging
import os
import json

from lib.metrics.routing_choice_metric import RoutingChoiceMetric
from lib.metrics.path_lengths_metric import PathLengthsMetric
from lib.metrics.graph_manager import GraphManager
from lib.metrics.experiment_config import ExperimentConfig
from lib.metrics.sender_set_calculator import SenderSetCalculator
from lib.metrics.sender_set_size import SenderSetSize, SenderSetSizeInterceptHop
from lib.metrics.adversary_intercept_hop import AdversaryInterceptHop, AdversaryInterceptHopCalculated
from lib.metrics.anonymity_metrics import AnonymityMetrics, AnonymityEntropy, AnonymityEntropyAtHop, AnonymityTopRankedSetSize
from lib.metrics.anonymity_accuracy_metrics import AnonymityAccuracyMetrics

from lib.file.file_finder import FileFinder, FileArchiver, FileCleaner
from lib.file.file_reader import JSONFileReader
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

        # can pass either full file path or directory path
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
        self.metrics = {'graphs': {}, 'data': {}, 'summations': {}}
        if not self.force_run and os.path.exists(self.metric_file_path):
            logging.debug('Loading an existing metric file')
            try:
                with open(self.metric_file_path, 'r') as metric_file:
                    self.metrics = json.loads(metric_file.read())
            except Exception as ex:
                # error reading storing metrics.json file, well fuck what do we do now
                # Panic obviously, but lets take shifts so we don't get tired
                raise Exception('unable to read : %s - %s' % (self.metric_file_path, str(ex)))

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
        archiver = FileArchiver(self.base_directory)
        archiver.process(self.base_directory, ['metrics.json', 'routing.json*'])
        cleaner = FileCleaner(self.base_directory)
        cleaner.process(self.base_directory, ['metrics.json'])

    def summarize(self):
        '''
        Run the summation metrics over a set of experiment repeats
        '''
        # load the metric data for each experiment repeat
        metric_managers = ClassLoader(MetricManager)
        finder = FileFinder([metric_managers])
        finder.process(self.base_directory, METRIC_FILE_NAME, True)
        # merge the repeat data into this metric instance
        merged_state = None
        for metric in metric_managers.class_instance:
            merged_state = self._merge(merged_state, metric)
        # Set the new metric data
        for group_name, metric_name, metric_obj in self._iter_store(merged_state):
            if not self._have_metric_data(group_name, metric_name):
                self._set_data(group_name, metric_name, metric_obj.to_csv())
        # run graph calculations
        return self.analyze()

    def analyze(self):
        '''
        Run experiment analysis
        :return: dict of the metric objects
        '''
        analysis_metrics = self._routing_choice()
        self._merge_store(analysis_metrics, self._experiment_config())
        self._merge_store(analysis_metrics, self._load_graphs())
        self._merge_store(analysis_metrics,
                          self._routing_paths(analysis_metrics))
        return analysis_metrics

    def _load_graphs(self):
        group_name = 'graph'
        metric_name = 'graph'
        graph_manager = GraphManager()
        # check if data is already available
        if self._have_metric_data(group_name, metric_name):
            graph_manager.load(self._get_data(group_name, metric_name))
        else:
            # No data available, get it
            search_dir = os.path.join(self.base_directory, 'graphs')
            finder = FileFinder([graph_manager])
            finder.process(search_dir, '*.gml')
            # store the results
            self._set_data(group_name, metric_name, graph_manager.to_csv())

        if self._get_sum(group_name, metric_name) is None:
            self._set_sum(group_name, metric_name,
                          graph_manager.create_summation())
        return {group_name: {metric_name: graph_manager}}

    def _experiment_config(self):
        exp_config = ExperimentConfig()
        metric_seq = [('variables', 'variables', exp_config)]
        search_dir = self.base_directory
        metric_dict = self._process_metrics(metric_seq, search_dir, 'config.json')
        self._set_config(exp_config.get_raw_config())
        return metric_dict

    def _routing_choice(self):
        metric_seq = [('routing', 'routing_choice', RoutingChoiceMetric())]
        search_dir = os.path.join(self.base_directory, 'graphs')
        return self._process_metrics(metric_seq, search_dir, '*.stats')

    def _routing_paths(self, analysis_metrics_dict):
        exp_config = self._get_store(
            'variables', 'variables', analysis_metrics_dict)
        graph_manager = self._get_store(
            'graph', 'graph', analysis_metrics_dict)
        routing_choice = self._get_store(
            'routing', 'routing_choice', analysis_metrics_dict)

        path_lengths = PathLengthsMetric()
        sender_set_calc = SenderSetCalculator(
            graph_manager, exp_config, routing_choice)
        sender_set_size = SenderSetSize(path_lengths)
        intercept_hop = AdversaryInterceptHop(sender_set_size)
        intercept_hop_calced = AdversaryInterceptHopCalculated(sender_set_size)
        sender_set_size_inter = SenderSetSizeInterceptHop(sender_set_size)

        anon_metrics = AnonymityMetrics()

        anon_entropy = AnonymityEntropy(anon_metrics, 'entropy', 'Entropy')
        anon_entropy_norm = AnonymityEntropy(
            anon_metrics, 'normalized_entropy', 'Entropy Normalized')
        anon_entropy_hop = AnonymityEntropyAtHop(
            anon_metrics, 'entropy', 'max_entropy', 'Entropy')
        anon_entropy_norm_hop = AnonymityEntropyAtHop(
            anon_metrics, 'normalized_entropy', '', 'Entropy Normalized')

        anon_entropy_act = AnonymityEntropy(
            anon_metrics, 'entropy_actual', 'Actual Entropy')
        anon_entropy_norm_act = AnonymityEntropy(
            anon_metrics, 'normalized_entropy_actual', 'Actual Entropy Normalized')
        anon_entropy_act_hop = AnonymityEntropyAtHop(
            anon_metrics, 'entropy_actual', 'max_entropy_actual', 'Actual Entropy')
        anon_entropy_act_norm_hop = AnonymityEntropyAtHop(
            anon_metrics, 'normalized_entropy_actual', '', 'Actual Entropy Normalized')

        top_ranked_set_avg = AnonymityTopRankedSetSize(anon_metrics)

        anon_accuracy_metrics = AnonymityAccuracyMetrics()

        metric_seq = [('routing', 'path_lengths', path_lengths),
                      ('sender_set', 'sender_set', sender_set_calc),
                      ('sender_set', 'sender_set_size', sender_set_size),
                      ('sender_set', 'sender_set_intercept_hop',
                       sender_set_size_inter),
                      ('adversary', 'intercept_hop', intercept_hop),
                      ('adversary', 'intercept_hop_calced', intercept_hop_calced),
                      ('anonymity', 'anonymity', anon_metrics),
                      ('anonymity', 'anonymity_entropy', anon_entropy),
                      ('anonymity', 'anonymity_entropy_normalized', anon_entropy_norm),
                      ('anonymity', 'anonymity_entropy_at_hop', anon_entropy_hop),
                      ('anonymity', 'anonymity_entropy_normalized_at_hop',
                       anon_entropy_norm_hop),
                      ('anonymity_actual', 'anonymity_entropy', anon_entropy_act),
                      ('anonymity_actual', 'anonymity_entropy_normalized',
                       anon_entropy_norm_act),
                      ('anonymity_actual', 'anonymity_entropy_at_hop',
                       anon_entropy_act_hop),
                      ('anonymity_actual', 'anonymity_entropy_normalized_at_hop',
                       anon_entropy_act_norm_hop),
                      ('anonymity_accuracy', 'anonymity_accuracy', anon_accuracy_metrics),
                      ('top_ranked', 'sender_set_size', top_ranked_set_avg)]
        search_dir = self.base_directory
        return self._process_metrics(metric_seq, search_dir, 'routing.json')

    def _process_metrics(self, metric_seq, folder_path, file_filter):
        # check if we already have the data for each metric
        metric_data = {}
        not_loaded_seq = []
        # try graphs first
        for g_name, m_name, metric in metric_seq:
            # data was found
            if self._have_metric_data(g_name, m_name):
                logging.debug('Loading existing data for %s:%s',
                              g_name, m_name)
                metric.load(self._get_data(g_name, m_name))
                # check if we have graph data
                if hasattr(metric, 'create_graph'):
                    if self._get_graph(g_name, m_name) is None:
                        logging.debug(
                            'Generating graph data from existing data')
                        self._set_graph(g_name, m_name, metric.create_graph())
                if hasattr(metric, 'create_summation'):
                    if self._get_sum(g_name, m_name) is None:
                        logging.debug(
                            'Generating metric data from existing data')
                        self._set_sum(g_name, m_name,
                                      metric.create_summation())
                self._add_store(g_name, m_name, metric, metric_data)
            # no existing data found, will need to calculate it later
            else:
                not_loaded_seq.append((g_name, m_name, metric))

        # run the missing graphs
        metrics_list = [m_inst for g_n, m_n, m_inst in not_loaded_seq]
        if len(metrics_list) > 0:
            file_reader = JSONFileReader(metrics_list)
            finder = FileFinder([file_reader])
            finder.process(folder_path, file_filter)
            # save the results of running the metrics
            for g_name, m_name, metric_obj in not_loaded_seq:
                self._set_data(g_name, m_name, metric_obj.to_csv())
                if hasattr(metric_obj, 'create_graph'):
                    self._set_graph(g_name, m_name, metric_obj.create_graph())
                if hasattr(metric_obj, 'create_summation'):
                    self._set_sum(g_name, m_name,
                                  metric_obj.create_summation())
                self._add_store(g_name, m_name, metric_obj, metric_data)
        return metric_data

    def _merge(self, merged_state, other_metric_manager):
        analysis_metrics = other_metric_manager.analyze()
        if merged_state is None:
            return analysis_metrics
        # merge the data sets
        for group_key, metric_key, metric_obj in self._iter_store(analysis_metrics):
            existing = self._get_store(group_key, metric_key, merged_state)
            # new entry?
            if existing is None:
                self._add_store(group_key, metric_key,
                                metric_obj, merged_state)
                continue
            # merge existing metrics
            existing.merge(metric_obj)
        return merged_state

    def _iter_store(self, metric_dic):
        for group_name, group_obj in metric_dic.items():
            for metric_name, metric_obj in group_obj.items():
                yield (group_name, metric_name, metric_obj)

    def _add_store(self, group_name, metric_name, metric_obj, metric_dict=None):
        if metric_dict is None:
            return {group_name: {metric_name: metric_obj}}
        if group_name not in metric_dict:
            metric_dict[group_name] = {}
        metric_dict[group_name][metric_name] = metric_obj
        return metric_dict

    def _get_store(self, group_name, metric_name, metric_dict):
        if group_name in metric_dict and metric_name in metric_dict[group_name]:
            return metric_dict[group_name][metric_name]
        return None

    def _merge_store(self, store_one, store_two):
        if store_one is None:
            return store_two
        for g_name, m_name, m_obj in self._iter_store(store_two):
            self._add_store(g_name, m_name, m_obj, store_one)
        return store_one

    def _have_metric_data(self, group_name, metric_name):
        return self._get_data(group_name, metric_name) is not None

    def _get_data(self, group_name, metric_name):
        return self._get_store(group_name, metric_name, self.metrics['data'])

    def _set_data(self, group_name, metric_name, value):
        self.is_dirty = True
        self._add_store(group_name, metric_name, value, self.metrics['data'])

    def _get_graph(self, group_name, metric_name):
        return self._get_store(group_name, metric_name, self.metrics['graphs'])

    def _set_graph(self, group_name, metric_name, value):
        self.is_dirty = True
        self._add_store(group_name, metric_name, value, self.metrics['graphs'])

    def _get_sum(self, group_name, metric_name):
        return self._get_store(group_name, metric_name, self.metrics['summations'])

    def _set_sum(self, group_name, metric_name, value):
        self.is_dirty = True
        self._add_store(group_name, metric_name, value,
                        self.metrics['summations'])

    def _set_config(self, value):
        self.is_dirty = True
        self.metrics['config'] = value
