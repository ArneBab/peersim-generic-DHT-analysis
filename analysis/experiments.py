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
from multiprocessing.pool import ThreadPool
import time

from lib.configuration import Configuration
from lib.file.executioner import Executioner
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
        total = self.setup_experiments(output_directory)
        self.run_experiments(total, args.p, output_directory, args.t)
        logging.info('Finished!!!')

    @timeit
    def setup_experiments(self, output_directory):
        '''
        Generate experiement configurationas and create file structure
        '''
        logging.info('setting up experiments ...')
        count = 0

        exp_file_path = os.path.join(output_directory, 'experiments.json')
        # load existing experiment configurations
        if os.path.exists(exp_file_path):
            with open(exp_file_path, 'r') as e_file:
                self._experiement_configurations = json.loads(e_file.read())
            count = len(self._experiement_configurations)
            logging.info('Loaded %s existing experiment configurations', count)

        # build the new experiment configurations
        config_manager = Configuration(output_directory)
        config_manager.build_configs()

        config_count = 1
        while config_manager.next():
            logging.info('Writing config %d of %d', config_count,
                         config_manager.get_total_count())
            config_count += 1

            exp_file_name = os.path.join(
                output_directory, config_manager.get_file_path(), 'config.cfg')
            exp_file_name = os.path.abspath(exp_file_name)
            dir_name = os.path.dirname(exp_file_name)

            config_file_name = os.path.join(dir_name, 'config.json')
            exp_archived = os.path.join(dir_name, 'archive.zip')

            # check if directory exists
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)

            # write the experiment config
            exp_files = {}
            current_config = config_manager.get_config()
            # hack to fix an issue
            # write the settings in JSON format for easy parsing
            with open(config_file_name, 'w') as c_file:
                c_file.write(json.dumps(current_config))
            # end hack
            # only write new files if there isn't already files there
            if os.path.exists(exp_archived):
                logging.info(
                    'Experiment already run and archived, skipping file write')
            elif not os.path.exists(exp_file_name) or not os.path.exists(config_file_name):
                with open(exp_file_name, 'w') as c_file:
                    c_file.write(config_manager.generate_experiement_config())
            else:
                logging.info(
                    'Experiment config already exists, skipping file write')

            config_file_name = config_file_name.replace(
                output_directory + os.sep, '')
            exp_file_name = exp_file_name.replace(
                output_directory + os.sep, '')

            # check if we need to add the experiment entry
            if not self._find(config_file_name):
                count += 1
                exp_files[CONST_EXPERIMENT] = exp_file_name
                exp_files[CONST_CONFIG] = config_file_name
                exp_files[CONST_GROUP] = config_manager.get_group_hash(
                    current_config)
                exp_files[CONST_ID] = count
                self._experiement_configurations.append(exp_files)

        with open(exp_file_path, 'w') as e_file:
            e_file.write(json.dumps(self._experiement_configurations))

        total = len(self._experiement_configurations)
        logging.info('Generated %s experiment configurations', total)
        return total

    def run_experiments(self, total, simulator_path, output_directory, threaded_count):
        '''
        Run the simulation for each experiment configuration
        '''
        # multi thread this
        nb_cores = threaded_count
        if threaded_count <= 0:
            nb_cores = multiprocessing.cpu_count()
        logging.info('Running experiments on %d threads', nb_cores)
        pool = ThreadPool(processes=nb_cores)

        experiment_count = 0
        for experiment_file in self._experiement_configurations:
            exp_file_path = os.path.join(
                output_directory, experiment_file[CONST_EXPERIMENT])
            experiment_count += 1

            if nb_cores > 1:
                pool.apply_async(_run_experiment, args=(
                    simulator_path, output_directory, exp_file_path, experiment_count, total))
            else:
                _run_experiment(
                    simulator_path, output_directory, exp_file_path, experiment_count, total)
        pool.close()
        pool.join()

    def _find(self, config_path):
        for exp in self._experiement_configurations:
            if exp[CONST_CONFIG] == config_path:
                return True
        return False


@timeit
def _run_experiment(simulator_path, output_directory, experiment_file, experiment_count, total):
    # set log level (can be lost if multiprocessing is used)
    logging.getLogger().setLevel(logging.INFO)

    logging.info('Running command %d of %d',
                 experiment_count, total)
    directory = os.path.dirname(experiment_file)

    exp_done = os.path.join(directory, 'experiment.done')
    if os.path.exists(exp_done):
        logging.info('Experiment already run ... skipping')
        return

    exp_archived = os.path.join(directory, 'archive.zip')
    if os.path.exists(exp_archived):
        logging.info('Experiment already run and archived ... skipping')
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
    PARSER.add_argument('-d', default='.', type=str, required=True,
                        help='Directory to store output in')
    PARSER.add_argument('-p', default='.', type=str, required=True,
                        help='Directory to find the PeerSim binaries in')
    PARSER.add_argument('-t', default='0', type=int,
                        help='Number of threads to run. Default is the # of core CPUs available')
    Experiments().main(PARSER.parse_args())
