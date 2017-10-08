# -*- coding: utf-8 -*-
'''
Updated on August, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Main class for running experiments and anaylzing results
'''
import logging
import argparse
import os
import json
import multiprocessing

from lib.configuration import ROUTING_DATA_FILE_NAME as R_F_NAME
from lib.analyzer import Analyzer
from lib.utils import timeit
from lib.summary_metrics import SummaryMetrics

CONST_EXPERIMENT = 'experiment'
CONST_CONFIG = 'config'
CONST_GROUP = 'repeat_group'


class Manager(object):
    '''
    Manages everything
    '''

    _experiement_configurations = []

    @timeit
    def main(self, args):
        '''
        Main entry point
        '''
        logging.info('Starting ...')

        total = self.load_experiments(args.d)
        self.run_analysis(total, args.f)
        self.run_summations(args.d, args.f)
        logging.info('Finished!!!')

    @timeit
    def load_experiments(self, output_directory):
        '''
        Generate experiement configurationas and create fiel structure
        '''
        logging.info('loading experiments ...')
        with open(os.path.join(output_directory, 'experiments.json'), 'r') as e_file:
            self._experiement_configurations = json.loads(e_file.read())

        total = len(self._experiement_configurations)
        logging.info('Loaded %s experiment configurations', total)
        return total

    @timeit
    def run_analysis(self, total, must_run):
        '''
        Run the post run analysis on a experiement
        '''

        # multi thread this
        nb_cores = multiprocessing.cpu_count()
        #nb_cores = max(nb_cores / 2, 1)
        logging.info('Running analysis on %d threads', nb_cores)
        pool = multiprocessing.Pool(processes=nb_cores)

        count = 1
        for exp_files in self._experiement_configurations:
            pool.apply_async(_run_analysis, args=(
                exp_files, count, total, must_run))
            #_run_analysis(exp_files, count, total, must_run)
            count += 1
        pool.close()
        pool.join()

    @timeit
    def run_summations(self, output_directory, must_run):
        '''
        Run after all experiments are complete. Compare the variables
        '''
        logging.info('Running experiment comparisions')
        # first calculate the average for each repeat group to average out anomylies
        exp_grouped = self._get_experiments_by_group(
            self._experiement_configurations)
        exp_group_count = len(exp_grouped.keys())
        count = 1
        groups = []
        for exp_files in exp_grouped.values():
            # base directory
            logging.info('Averaging group %d of %d', count, exp_group_count)
            count += 1

            first_exp = exp_files[0]
            base_path = _get_base(_get_base(first_exp[CONST_CONFIG]))
            groups.append(_metrics(base_path, 'consolidated.json'))

            # check if we can skip running the summation
            if not must_run and os.path.exists(_metrics(base_path, 'consolidated.json')):
                logging.info('Already analyzed group ... skipping')
                continue

            conf_files = [exp[CONST_CONFIG] for exp in exp_files]

            analyzer = Analyzer(conf_files)
            if not os.path.exists(_metrics(base_path)):
                os.makedirs(_metrics(base_path))

            # routing choice stats
            with open(_metrics(base_path, 'stats.json'), 'w') as s_file:
                routing_choice_avg, graph_data = analyzer.run_routing_choice_metrics()
                s_file.write(json.dumps(graph_data))

            r_metrics = analyzer.get_routing_metrics(None, None, None)
            r_metrics.calculate_metrics()
            _write_analysis_data(base_path, r_metrics)

        # caluclate the summary comparision of the experiment runs
        summary = SummaryMetrics()
        with open(os.path.join(output_directory, 'summary.json'), 'w') as s_file:
            s_file.write(json.dumps(summary.calculate(groups)))

    def _get_experiments_by_group(self, experiments):
        by_groups = {}
        for exp in experiments:
            if exp[CONST_GROUP] not in by_groups:
                by_groups[exp[CONST_GROUP]] = []
            by_groups[exp[CONST_GROUP]].append(exp)
        return by_groups


def _get_base(path):
    return os.path.dirname(path)


def _base(base_path, *args):
    path = base_path
    if args:
        for sec in args:
            path = os.path.join(path, sec)
    return path


def _metrics(base_path, *args):
    path = os.path.join(base_path, 'metrics')
    if args:
        for sec in args:
            path = os.path.join(path, sec)
    return path


def _run_analysis(exp_files, count, total, must_run):
    logging.info('Running analysis %d of %d', count, total)

    # base directory
    base_path = _get_base(exp_files[CONST_CONFIG])

    # skip analysis if it alreay done
    if not must_run and os.path.exists(_metrics(base_path, 'intercept_calculated.json')):
        logging.info('Already analyzed ... skipping')
        return

    analyzer = Analyzer([exp_files[CONST_CONFIG]])
    if not os.path.exists(_metrics(base_path)):
        os.makedirs(_metrics(base_path))

    # routing choice stats
    with open(_metrics(base_path, 'stats.json'), 'w') as s_file:
        routing_choice_avg, graph_data = analyzer.run_routing_choice_metrics()
        s_file.write(json.dumps(graph_data))

    # routing metrics
    routing_data_name = _base(base_path, R_F_NAME)
    new_routing_data = _base(base_path, 'processed.' + R_F_NAME)

    r_metrics = analyzer.get_routing_metrics(
        routing_data_name, new_routing_data, routing_choice_avg)
    r_metrics.calculate_metrics()
    _write_analysis_data(base_path, r_metrics)


def _write_analysis_data(base_path, r_metrics):
    # path length
    with open(_metrics(base_path, 'path_histo.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.graph_path_lengths()))
    # anon metrics
    with open(_metrics(base_path, 'sender_set_size.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.graph_sender_set()))

    with open(_metrics(base_path, 'sender_set_size_by_hop.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.graph_sender_set_by_hop()))
    # entropy metrics
    with open(_metrics(base_path, 'entropy.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.graph_entropy()))
    with open(_metrics(base_path, 'entropy_normalized.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.graph_entropy_normalized()))

    with open(_metrics(base_path, 'entropy_by_hop.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.graph_entropy_by_hop()))
    with open(_metrics(base_path, 'entropy_normalized_by_hop.json'), 'w') as g_file:
        g_file.write(json.dumps(
            r_metrics.graph_entropy_normalized_by_hop()))

    with open(_metrics(base_path, 'top_rank_set_size_by_hop.json'), 'w') as g_file:
        g_file.write(json.dumps(
            r_metrics.graph_top_rank_set_size_by_hop()))

    with open(_metrics(base_path, 'top_rank_by_hop.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.graph_top_rank_by_hop()))
    # entropy metric using actual backoff
    with open(_metrics(base_path, 'entropy_actual.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.graph_entropy_actual()))
    with open(_metrics(base_path, 'entropy_normalized_actual.json'), 'w') as g_file:
        g_file.write(json.dumps(
            r_metrics.graph_entropy_normalized_actual()))

    with open(_metrics(base_path, 'entropy_by_hop_actual.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.graph_entropy_by_hop_actual()))
    with open(_metrics(base_path, 'entropy_normalized_by_hop_actual.json'), 'w') as g_file:
        g_file.write(json.dumps(
            r_metrics.graph_entropy_normalized_by_hop_actual()))

    # consolidated metrics
    with open(_metrics(base_path, 'consolidated.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.get_summary()))
    # intercept hop
    with open(_metrics(base_path, 'intercept.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.graph_intercept_hop()))
    with open(_metrics(base_path, 'intercept_percent.json'), 'w') as g_file:
        g_file.write(json.dumps(r_metrics.graph_intercept_percent_hop()))
    # intercept hop
    with open(_metrics(base_path, 'intercept_calculated.json'), 'w') as g_file:
        g_file.write(json.dumps(
            r_metrics.graph_intercept_hop_calculated()))


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    PARSER = argparse.ArgumentParser(
        description='Run some Anonymous P2P DHT experiments.')
    PARSER.add_argument('-d', default='.', type=str,
                        help='Directory to store output in')
    PARSER.add_argument('-f', default=False, action='store_true',
                        help='Force the experiments to rerun')
    Manager().main(PARSER.parse_args())