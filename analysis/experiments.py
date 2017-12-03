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

from lib.configuration import Configuration
from lib.configuration import ROUTING_DATA_FILE_NAME as R_F_NAME
from lib.executioner import Executioner
from lib.analyzer import Analyzer
from lib.utils import timeit
from lib.summary_metrics import SummaryMetrics

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

        total = self.setup_experiments(args.d)
        self.run_experiments(total, args.p, args.t)
        logging.info('Finished!!!')

    @timeit
    def setup_experiments(self, output_directory):
        '''
        Generate experiement configurationas and create fiel structure
        '''
        logging.info('setting up experiments ...')
        count = 1

        config_manager = Configuration(output_directory)
        config_manager.build_configs()
        
        while config_manager.next():
            logging.info('Writing config %d of %d' % (count, config_manager.get_total_count()))
            
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
            # only write new files if there isn't already fiels there
            if not os.path.exists(exp_file_name) or not os.path.exists(config_file_name):
                with open(exp_file_name, 'w') as c_file:
                    c_file.write(config_manager.generate_experiement_config())
                # write the settings in JSON format for easy parsing
                with open(config_file_name, 'w') as c_file:
                    c_file.write(json.dumps(current_config))
            else:
                logging.info('Experiment config already exists, skipping file write')

            exp_files[CONST_EXPERIMENT] = exp_file_name
            exp_files[CONST_CONFIG] = config_file_name
            exp_files[CONST_GROUP] = config_manager.get_group_hash(current_config)
            exp_files[CONST_ID] = count
            self._experiement_configurations.append(exp_files)
            count += 1

        with open(os.path.join(output_directory, 'experiments.json'), 'w') as e_file:
            e_file.write(json.dumps(self._experiement_configurations))

        total = len(self._experiement_configurations)
        logging.info('Generated %s experiment configurations', total)
        return total

    def run_experiments(self, total, simulator_path, threaded):
        '''
        Run the simulation for each experiment configuration
        '''

        # multi thread this
        nb_cores = multiprocessing.cpu_count() / 2
        if threaded:
            logging.info('Running experiments on %d threads', nb_cores)
        pool = multiprocessing.Pool(processes=nb_cores)

        experiment_count = 0
        for experiment_file in self._experiement_configurations:
            experiment_count += 1
            if threaded:
                pool.apply_async(_run_experiment, args=(
                    simulator_path, experiment_file[CONST_EXPERIMENT]))
            else:
                _run_experiment(simulator_path, experiment_file[CONST_EXPERIMENT])
            logging.info('Running command %d of %d',
                         experiment_count, total)
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
def _run_experiment(simulator_path, experiment_file):
    directory = os.path.dirname(experiment_file)
    if os.path.exists(os.path.join(directory, 'routing.json')):
        logging.info('Experiment already run ... skipping')
        return
    
    exp = Executioner(simulator_path)
    exit_code = exp.run(experiment_file)
    if exit_code > 0:
        logging.error('Returned exit code %d', exit_code)
        raise Exception('Simulator failed to run: %s', experiment_file)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    PARSER = argparse.ArgumentParser(
        description='Run some Anonymous P2P DHT experiments.')
    PARSER.add_argument('-d', default='.', type=str,
                        help='Directory to store output in')
    PARSER.add_argument('-p', default='.', type=str,
                        help='Directory to find the PeerSim binaries in')
    PARSER.add_argument('-t', default=True, action='store_false',
                        help='Run experiments in seperate threads')
    Experiments().main(PARSER.parse_args())
