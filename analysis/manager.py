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

from lib.configuration import Configuration
from lib.executioner import Executioner
from lib.analyzer import Analyzer

CONST_EXPERIMENT = 'experiment'
CONST_CONFIG = 'config'
CONST_STAT_GRAPH_FILE_NAME = 'stats.json'
CONST_METRICS_DIR = 'metrics'


class Manager(object):
    '''
    Manages everything
    '''

    _experiement_configurations = []

    def main(self, args):
        '''
        Main entry point
        '''
        logging.info('Starting ...')
        self.setup_experiments(args.d)
        self.run_experiments(args.p)
        self.run_analysis()
        logging.info('Finished!!!')

    def setup_experiments(self, output_directory):
        '''
        Generate experiement configurationas and create fiel structure
        '''
        logging.info('setting up experiments ...')
        config_manager = Configuration(output_directory)
        while config_manager.next():
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
            with open(exp_file_name, 'w') as c_file:
                c_file.write(config_manager.generate_experiement_config())
                exp_files[CONST_EXPERIMENT] = exp_file_name
            # write the settings in JSON format for easy parsing
            with open(config_file_name, 'w') as c_file:
                c_file.write(json.dumps(config_manager.get_config()))
                exp_files[CONST_CONFIG] = config_file_name
            self._experiement_configurations.append(exp_files)

        with open(os.path.join(output_directory, 'experiments.json'), 'w') as e_file:
            e_file.write(json.dumps(self._experiement_configurations))

        logging.info('Generated %s experiment configurations',
                     len(self._experiement_configurations))

    def run_experiments(self, simulator_path):
        '''
        Run the simulation for each experiment configuration
        '''
        experiment_count = 1
        for experiment_file in self._experiement_configurations:
            logging.info('Running command %d of %d',
                         experiment_count, len(self._experiement_configurations))
            experiment_count = experiment_count + 1

            exp = Executioner(simulator_path)
            exit_code = exp.run(experiment_file[CONST_EXPERIMENT])
            if exit_code > 0:
                logging.error('Returned exit code %d', exit_code)
                raise Exception('Simulator failed to run')

    def run_analysis(self):
        '''
        Run the post run analysis on each experiement
        '''
        count = 1
        for experiment_file in self._experiement_configurations:
            logging.info('Running analysis %d of %d',
                         count, len(self._experiement_configurations))
            count = count + 1

            analyzer = Analyzer(experiment_file[CONST_CONFIG])
            if not os.path.exists(os.path.join(analyzer.base_data_directory,
                                               CONST_METRICS_DIR)):
                os.makedirs(os.path.join(analyzer.base_data_directory,
                                         CONST_METRICS_DIR))
            # routing choice stats
            with open(os.path.join(analyzer.base_data_directory, CONST_METRICS_DIR,
                                   CONST_STAT_GRAPH_FILE_NAME), 'w') as s_file:
                s_file.write(json.dumps(analyzer.run_routing_choice_metrics()))

            routing_metrics = analyzer.run_routing_metrics()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    PARSER = argparse.ArgumentParser(
        description='Run some Anonymous P2P DHT experiments.')
    PARSER.add_argument('-d', default='.', type=str,
                        help='Directory to store output in')
    PARSER.add_argument('-p', default='.', type=str,
                        help='Directory to find the PeerSim binaries in')
    Manager().main(PARSER.parse_args())
