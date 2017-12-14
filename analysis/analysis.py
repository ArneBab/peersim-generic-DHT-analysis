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

from lib.utils import timeit
#from lib.summary_metrics import SummaryMetrics

from lib.metric_manager import MetricManager

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

        output_directory = os.path.abspath(args.d)
        total = self.load_experiments(output_directory)
        self.run_analysis(total, args.f, args.t)
        self.run_summations(args.f, args.t)
        logging.info('Finished!!!')

    @timeit
    def load_experiments(self, output_directory):
        '''
        Generate experiement configurationas and create fiel structure
        '''
        logging.info('loading experiments ...')
        with open(os.path.join(output_directory, 'experiments.json'), 'r') as e_file:
            self._experiement_configurations = json.loads(e_file.read())

        # make the paths absolute
        for exp_files in self._experiement_configurations:
            exp_files[CONST_CONFIG] = os.path.join(
                output_directory, exp_files[CONST_CONFIG])
            exp_files[CONST_EXPERIMENT] = os.path.join(
                output_directory, exp_files[CONST_EXPERIMENT])

        total = len(self._experiement_configurations)
        logging.info('Loaded %s experiment configurations', total)
        return total

    @timeit
    def run_analysis(self, total, must_run, thread_count):
        '''
        Run the post run analysis on a experiement
        '''

        # multi thread this
        nb_cores = thread_count
        if thread_count <= 0:
            nb_cores = multiprocessing.cpu_count()
        logging.info('Running experiments on %d threads', nb_cores)
        pool = multiprocessing.Pool(processes=nb_cores)

        count = 1
        for exp_files in self._experiement_configurations:
            if nb_cores > 1:
                pool.apply_async(_run_analysis, args=(
                    exp_files, count, total, must_run))
            else:
                _run_analysis(exp_files,
                              count, total, must_run)
            count += 1
        pool.close()
        pool.join()

    @timeit
    def run_summations(self, must_run, thread_count):
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

        # multi thread this
        nb_cores = thread_count
        if thread_count <= 0:
            nb_cores = multiprocessing.cpu_count()
        logging.info('Running analysis on %d threads', nb_cores)
        pool = multiprocessing.Pool(processes=nb_cores)

        for exp_files in exp_grouped.values():
            if nb_cores > 1:
                groups.append(pool.apply_async(_run_summations, args=(
                    exp_files, count, exp_group_count, must_run)))
            else:
                groups.append(_run_summations(
                    exp_files, count, exp_group_count, must_run))
            count += 1
        pool.close()
        pool.join()

        # get the async results
        if thread_count > 1:
            holder = [result.get() for result in groups]
            groups = holder

        ## caluclate the summary comparision of the experiment runs
        #summary = SummaryMetrics()
        #experiment_data = summary.calculate(groups)
        #with open(os.path.join(output_directory, 'summary.json'), 'w') as s_file:
        #    s_file.write(json.dumps(experiment_data))

        #with open(os.path.join(output_directory, 'summary_display.json'), 'w') as s_file:
        #    s_file.write(json.dumps(summary.process(experiment_data)))

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


def _run_summations(exp_files, count, total, must_run):
    # base directory
    logging.info('Averaging group %d of %d', count, total)
    count += 1

    first_exp = exp_files[0]
    base_path = _get_base(_get_base(first_exp[CONST_CONFIG]))

    metric_manager = MetricManager(base_path, must_run)
    metric_manager.summarize()
    metric_manager.save_data()
    return metric_manager.metric_file_path


def _run_analysis(exp_files, count, total, must_run):
    logging.info('Running analysis %d of %d', count, total)

    # base directory
    base_path = _get_base(exp_files[CONST_CONFIG])

    # calculate analysis metrics
    metric_manager = MetricManager(base_path, must_run)
    metric_manager.analyze()
    metric_manager.save_data()
    metric_manager.archive_data()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    PARSER = argparse.ArgumentParser(
        description='Run some Anonymous P2P DHT experiment analysis.')
    PARSER.add_argument('-d', default='.', type=str,
                        help='Directory to store output in')
    PARSER.add_argument('-f', default=False, action='store_true',
                        help='Force the analysis to rerun')
    PARSER.add_argument('-t', default='0', type=int,
                        help='Number of threads to run. Default is the # of core CPUs available')
    Manager().main(PARSER.parse_args())
