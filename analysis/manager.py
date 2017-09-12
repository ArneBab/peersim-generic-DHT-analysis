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
from lib.configuration import ROUTING_DATA_FILE_NAME as R_F_NAME
from lib.executioner import Executioner
from lib.analyzer import Analyzer

CONST_EXPERIMENT = 'experiment'
CONST_CONFIG = 'config'


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

            # base directory
            base_path = self._get_base(experiment_file[CONST_CONFIG])

            analyzer = Analyzer(experiment_file[CONST_CONFIG])
            if not os.path.exists(self._metrics(base_path)):
                os.makedirs(self._metrics(base_path))

            # routing choice stats
            with open(self._metrics(base_path, 'stats.json'), 'w') as s_file:
                s_file.write(json.dumps(analyzer.run_routing_choice_metrics()))

            # routing metrics
            routing_data_name = self._base(base_path, R_F_NAME)
            new_routing_data = self._base(base_path, 'processed.' + R_F_NAME)

            r_metrics = analyzer.get_routing_metrics(
                routing_data_name, new_routing_data)
            r_metrics.calculate_metrics()

            # path length
            with open(self._metrics(base_path, 'path_histo.json'), 'w') as g_file:
                g_file.write(json.dumps(r_metrics.graph_path_lengths()))
            # graph metrics
            with open(self._metrics(base_path, 'graphs.json'), 'w') as g_file:
                g_file.write(json.dumps(r_metrics.graph_metrics()))
            # anon metrics
            with open(self._metrics(base_path, 'anon_set.json'), 'w') as g_file:
                g_file.write(json.dumps(r_metrics.graph_anonymity_set()))
            # entropy metrics
            with open(self._metrics(base_path, 'entropy.json'), 'w') as g_file:
                g_file.write(json.dumps(r_metrics.graph_entropy()))
            # consolidated metrics
            with open(self._metrics(base_path, 'consolidated.json'), 'w') as g_file:
                g_file.write(json.dumps(r_metrics.get_summary()))
            # intercept hop
            with open(self._metrics(base_path, 'intercept.json'), 'w') as g_file:
                g_file.write(json.dumps(r_metrics.graph_intercept_hop()))
            # intercept hop
            with open(self._metrics(base_path, 'intercept_calculated.json'), 'w') as g_file:
                g_file.write(json.dumps(
                    r_metrics.graph_intercept_hop_calculated()))

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


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    PARSER = argparse.ArgumentParser(
        description='Run some Anonymous P2P DHT experiments.')
    PARSER.add_argument('-d', default='.', type=str,
                        help='Directory to store output in')
    PARSER.add_argument('-p', default='.', type=str,
                        help='Directory to find the PeerSim binaries in')
    Manager().main(PARSER.parse_args())
