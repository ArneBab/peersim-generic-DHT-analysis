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
import time
import datetime

from lib.configuration import Configuration
from lib.executioner import Executioner
from lib.utils import timeit

CONST_EXPERIMENT = 'experiment'
CONST_CONFIG = 'config'
CONST_GROUP = 'repeat_group'
CONST_ID = 'id'


class Experiments(object):
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
        total = self.setup_experiments(output_directory, args.f)
        self.run_experiments(total, args.p, output_directory, args.t, args.m)
        logging.info('Finished!!!')

    @timeit
    def setup_experiments(self, output_directory, must_run):
        '''
        Generate experiement configurationas and create fiel structure
        '''
        exp_file_path = os.path.join(output_directory, 'experiments.json')
        # load existing experiment configurations
        if not must_run and os.path.exists(exp_file_path):
            with open(exp_file_path, 'r') as e_file:
                self._experiement_configurations = json.loads(e_file.read())
            total = len(self._experiement_configurations)
            logging.info('Loaded %s existing experiment configurations', total)
            return total

        logging.info('setting up experiments ...')
        count = 1

        config_manager = Configuration(output_directory)
        config_manager.build_configs()

        while config_manager.next():
            logging.info('Writing config %d of %d', count,
                         config_manager.get_total_count())

            exp_file_name = os.path.join(
                output_directory, config_manager.get_file_path(), 'config.cfg')
            exp_file_name = os.path.abspath(exp_file_name)
            dir_name = os.path.dirname(exp_file_name)

            config_file_name = os.path.join(dir_name, 'config.json')

            # check if directory exists
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)

            # write the experiment config
            exp_files = {}
            current_config = config_manager.get_config()
            # only write new files if there isn't already files there
            if not os.path.exists(exp_file_name) or not os.path.exists(config_file_name) or \
               must_run:
                with open(exp_file_name, 'w') as c_file:
                    c_file.write(config_manager.generate_experiement_config())
                # write the settings in JSON format for easy parsing
                with open(config_file_name, 'w') as c_file:
                    c_file.write(json.dumps(current_config))
            else:
                logging.info(
                    'Experiment config already exists, skipping file write')

            exp_files[CONST_EXPERIMENT] = exp_file_name.replace(
                output_directory + os.sep, '')
            exp_files[CONST_CONFIG] = config_file_name.replace(
                output_directory + os.sep, '')
            exp_files[CONST_GROUP] = config_manager.get_group_hash(
                current_config)
            exp_files[CONST_ID] = count
            self._experiement_configurations.append(exp_files)
            count += 1

        with open(exp_file_path, 'w') as e_file:
            e_file.write(json.dumps(self._experiement_configurations))

        total = len(self._experiement_configurations)
        logging.info('Generated %s experiment configurations', total)
        return total

    def run_experiments(self, total, simulator_path, output_directory, threaded_ratio, multiplexor):
        '''
        Run the simulation for each experiment configuration
        '''
        # parse the multiplexor
        exp_mod = int(multiplexor.split(':')[0])
        exp_mod_cond = int(multiplexor.split(':')[1])

        # multi thread this
        nb_cores = multiprocessing.cpu_count()
        if threaded_ratio > 0:
            nb_cores = nb_cores / threaded_ratio
            logging.info('Running experiments on %d threads', nb_cores)
        pool = multiprocessing.Pool(processes=nb_cores)

        experiment_count = 0
        for experiment_file in self._experiement_configurations:
            exp_file_path = os.path.join(
                output_directory, experiment_file[CONST_EXPERIMENT])
            experiment_count += 1

            # determine if this process is responsible for this experiment
            if experiment_count % exp_mod != exp_mod_cond:
                logging.info('Another process is running command %d of %d',
                             experiment_count, total)
                continue

            if threaded_ratio > 0:
                pool.apply_async(_run_experiment, args=(
                    simulator_path, output_directory, exp_file_path, experiment_count, total))
            else:
                _run_experiment(
                    simulator_path, output_directory, exp_file_path, experiment_count, total)
        pool.close()
        pool.join()

    def _get_base(self, path):
        return os.path.dirname(path)

    def _base(self, base_path, *args):
        path = base_path
        if args:
            for sec in args:
                path = os.path.join(path, sec)
        return path

    def _metrics(self, base_path, *args):
        path = os.path.join(base_path, 'metrics')
        if args:
            for sec in args:
                path = os.path.join(path, sec)
        return path


@timeit
def _run_experiment(simulator_path, output_directory, experiment_file, experiment_count, total):
    logging.info('Running command %d of %d',
                 experiment_count, total)
    directory = os.path.dirname(experiment_file)

    exp_done = os.path.join(directory, 'experiment.done')
    if os.path.exists(exp_done):
        logging.info('Experiment already run ... skipping')
        return

    exp = Executioner(simulator_path)
    exit_code = exp.run(experiment_file, output_directory)
    if exit_code > 0:
        logging.error('Returned exit code %d', exit_code)
        raise Exception('Simulator failed to run: %s' % experiment_file)

    # mark this experiment as complete
    with open(exp_done, 'w') as run_time_file:
        run_time_file.write(str(time.time()))


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    PARSER = argparse.ArgumentParser(
        description='Run some Anonymous P2P DHT experiments.')
    PARSER.add_argument('-d', default='.', type=str,
                        help='Directory to store output in')
    PARSER.add_argument('-p', default='.', type=str,
                        help='Directory to find the PeerSim binaries in')
    PARSER.add_argument('-m', default='1:0', type=str,
                        help='Multiple processes running experiments. Experiment # mod 1 == 0')
    PARSER.add_argument('-f', default=False, action='store_true',
                        help='Force the experiments to rerun')
    PARSER.add_argument('-t', default='1', type=int,
                        help='Ratio of thread to use 1/t threads. Default is 1/1.')
    Experiments().main(PARSER.parse_args())
