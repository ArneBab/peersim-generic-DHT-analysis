# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Manage all of the analysis metrics
'''
import logging
import os
import json

from lib.actions.routing_choice_metric import RoutingChoiceMetric
from lib.actions.path_lengths_metric import PathLengthsMetric
from lib.actions.graph_manager import GraphManager
from lib.actions.experiment_config import ExperimentConfig
from lib.actions.sender_set_calculator import SenderSetCalculator
from lib.actions.sender_set_size import SenderSetSize, SenderSetSizeInterceptHop
from lib.actions.adversary_intercept_hop import AdversaryInterceptHop
from lib.actions.adversary_intercept_hop import AdversaryInterceptHopCalculated
from lib.actions.anonymity_metrics import AnonymityMetrics, AnonymityEntropy
from lib.actions.anonymity_metrics import AnonymityEntropyAtHop, AnonymityTopRankedSetSize
from lib.actions.anonymity_accuracy_metrics import AnonymityAccuracyMetrics
from lib.actions.merge.metric_merger import MetricManagerMerger
from lib.actions.merge.metric_comparer import MetricManagerComparer, SummationVariableComparer

from lib.file.file_finder import FileFinder, FileArchiver, FileCleaner
from lib.file.file_reader import JSONFileReader, ClassReader

from lib.utils import metric_iter, metric_add, metric_get, metric_merge
from lib.configuration import Configuration


METRIC_FILE_NAME = 'metrics.json'


class MetricManager(object):
    '''
    Manage all of the analysis metrics for a given experiment
    '''

    def __init__(self, base_directory, experiment_id=''):
        base_directory = os.path.abspath(base_directory)
        if not os.path.exists(base_directory):
            raise Exception('Unable to find the directory: %s' %
                            base_directory)

        self.is_dirty = False
        self.experiment_id = str(experiment_id)

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
        self.metrics = {'graphs': {}, 'data': {}, 'summations': {}, 'config': None}
        if os.path.exists(self.metric_file_path):
            logging.debug('Loading an existing metric file')
            try:
                with open(self.metric_file_path, 'r') as metric_file:
                    self.metrics = json.loads(metric_file.read())
            except Exception as ex:
                # error reading storing metrics.json file, well fuck what do we do now
                # Panic obviously, but lets take shifts so we don't get tired
                raise Exception('unable to read : %s - %s' %
                                (self.metric_file_path, str(ex)))

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
        if not archiver.exists():

            logging.info(' -- %s -- Archiving experiment data',
                         self.experiment_id)
            archiver.process(self.base_directory,
                             ['metrics.json', 'routing.json*'])
            cleaner = FileCleaner(self.base_directory)
            cleaner.process(self.base_directory, ['metrics.json'])

    def compare_experiments(self, experiment_metric_file_paths):
        '''
        Run analysis the compares the output from each experiment
        :param experiment_metric_file_paths: List of the metric files
         for each of the experiments
        :return: dict of the metric objects
        '''
        # pivot data and generate graph for each metric
        for variable in Configuration.get_parameters():
            if variable == 'repeat':
                continue
            # get metrics for variable
            cmp_exps = MetricManagerComparer(variable)
            class_reader = ClassReader([cmp_exps], MetricManager)
            finder = FileFinder([class_reader])
            finder.process_file_list(
                self.base_directory, experiment_metric_file_paths)

            for group_name, metric_name, position in metric_iter(cmp_exps.metric_map):
                if group_name == 'variables':
                    continue

                metric_cmp = SummationVariableComparer(
                    cmp_exps, metric_name)
                metric_cmp.process(None)
                self._set_data(metric_cmp.to_csv(True), variable, group_name, metric_name)
                self._set_graph(metric_cmp.create_graph(), variable, group_name, metric_name)

    def summarize(self):
        '''
        Run the summation metrics over a set of experiment repeats
        '''
        # load the metric data for each experiment repeat
        avg_repeat_exps = MetricManagerMerger()
        class_reader = ClassReader([avg_repeat_exps], MetricManager)
        finder = FileFinder([class_reader])
        finder.process(self.base_directory, METRIC_FILE_NAME, True)
        # Set the new metric data
        self._set_config(avg_repeat_exps.get_merged_config())
        merged_data = avg_repeat_exps.get_merged_data()
        for group_name, metric_name, metric_obj in metric_iter(merged_data):
            if not self._have_metric_data(group_name, metric_name):
                self._set_data(metric_obj.to_csv(), group_name, metric_name)
        # run graph calculations
        return self.analyze()

    def analyze(self):
        '''
        Run experiment analysis
        :return: dict of the metric objects
        '''
        analysis_metrics = self._routing_choice()
        metric_merge(analysis_metrics, self._experiment_config())
        metric_merge(analysis_metrics, self._load_graphs())
        metric_merge(analysis_metrics, self._routing_paths(analysis_metrics))
        return analysis_metrics

    def get_config(self):
        '''
        Get the experiment configuration
        :return: dict of the configuration objects
        '''
        return self.metrics['config']

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
            self._set_data(graph_manager.to_csv(), group_name, metric_name)

        if self._get_sum(group_name, metric_name) is None:
            self._set_sum(graph_manager.create_summation(), group_name, metric_name)
        return {group_name: {metric_name: graph_manager}}

    def _experiment_config(self):
        exp_config = ExperimentConfig()
        metric_seq = [('variables', 'variables', exp_config)]
        search_dir = self.base_directory
        metric_dict = self._process_metrics(
            metric_seq, search_dir, 'config.json')
        if exp_config.get_raw_config() is not None:
            self._set_config(exp_config.get_raw_config())
        return metric_dict

    def _routing_choice(self):
        metric_seq = [('routing', 'routing_choice', RoutingChoiceMetric())]
        search_dir = os.path.join(self.base_directory, 'graphs')
        return self._process_metrics(metric_seq, search_dir, '*.stats')

    def _routing_paths(self, analysis_metrics_dict):
        exp_config = metric_get(
            'variables', 'variables', analysis_metrics_dict)
        graph_manager = metric_get(
            'graph', 'graph', analysis_metrics_dict)
        routing_choice = metric_get(
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
                      ('anonymity_accuracy', 'anonymity_accuracy',
                       anon_accuracy_metrics),
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
                        self._set_graph(metric.create_graph(), g_name, m_name)
                if hasattr(metric, 'create_summation'):
                    if self._get_sum(g_name, m_name) is None:
                        logging.debug(
                            'Generating metric data from existing data')
                        self._set_sum(metric.create_summation(), g_name, m_name)
                metric_add(metric, metric_data, g_name, m_name)
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
                self._set_data(metric_obj.to_csv(), g_name, m_name)
                if hasattr(metric_obj, 'create_graph'):
                    self._set_graph(metric_obj.create_graph(), g_name, m_name)
                if hasattr(metric_obj, 'create_summation'):
                    self._set_sum(metric_obj.create_summation(), g_name, m_name)
                metric_add(metric_obj, metric_data, g_name, m_name)
        return metric_data

    def _have_metric_data(self, group_name, metric_name):
        return self._get_data(group_name, metric_name) is not None

    def _get_data(self, group_name, metric_name):
        return metric_get(group_name, metric_name, self.metrics['data'])

    def _set_data(self, value, *args):
        self.is_dirty = True
        metric_add(value, self.metrics['data'], *args)

    def _get_graph(self, group_name, metric_name):
        return metric_get(group_name, metric_name, self.metrics['graphs'])

    def _set_graph(self, value, *args):
        self.is_dirty = True
        metric_add(value, self.metrics['graphs'], *args)

    def _get_sum(self, group_name, metric_name):
        return metric_get(group_name, metric_name, self.metrics['summations'])

    def _set_sum(self, value, *args):
        self.is_dirty = True
        metric_add(value, self.metrics['summations'], *args)

    def _set_config(self, value):
        self.is_dirty = True
        self.metrics['config'] = value
