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
CONST_GROUP = 'repeat_group'


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

        total = self.setup_experiments(args.d)
        for count, exp_files in self.run_experiments(total, args.p):
            self.run_analysis(count, total, exp_files)
        self.run_summations()
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
            current_config = config_manager.get_config()
            with open(config_file_name, 'w') as c_file:
                c_file.write(json.dumps(current_config))
            exp_files[CONST_CONFIG] = config_file_name
            exp_files[CONST_GROUP] = config_manager.get_group_hash(current_config)
            self._experiement_configurations.append(exp_files)

        with open(os.path.join(output_directory, 'experiments.json'), 'w') as e_file:
            e_file.write(json.dumps(self._experiement_configurations))

        total = len(self._experiement_configurations)
        logging.info('Generated %s experiment configurations', total)
        return total

    def run_experiments(self, total, simulator_path):
        '''
        Run the simulation for each experiment configuration
        '''
        experiment_count = 0
        for experiment_file in self._experiement_configurations:
            experiment_count += 1
            logging.info('Running command %d of %d',
                         experiment_count, total)

            exp = Executioner(simulator_path)
            exit_code = exp.run(experiment_file[CONST_EXPERIMENT])
            if exit_code > 0:
                logging.error('Returned exit code %d', exit_code)
                raise Exception('Simulator failed to run')

            yield experiment_count, experiment_file

    def run_analysis(self, count, total, exp_files):
        '''
        Run the post run analysis on a experiement
        '''
        logging.info('Running analysis %d of %d', count, total)

        # base directory
        base_path = self._get_base(exp_files[CONST_CONFIG])

        analyzer = Analyzer([exp_files[CONST_CONFIG]])
        if not os.path.exists(self._metrics(base_path)):
            os.makedirs(self._metrics(base_path))

        # routing choice stats
        with open(self._metrics(base_path, 'stats.json'), 'w') as s_file:
            routing_choice_avg, graph_data = analyzer.run_routing_choice_metrics()
            s_file.write(json.dumps(graph_data))

        # routing metrics
        routing_data_name = self._base(base_path, R_F_NAME)
        new_routing_data = self._base(base_path, 'processed.' + R_F_NAME)

        r_metrics = analyzer.get_routing_metrics(
            routing_data_name, new_routing_data, routing_choice_avg)
        r_metrics.calculate_metrics()
        self._write_analysis_data(base_path, r_metrics)


    def run_summations(self):
        '''
        Run after all experiments are complete. Compare the variables
        '''
        logging.info('Running experiment comparisions')
        # first calculate the average for each repeat group to average out anomylies
        exp_grouped = self._get_experiments_by_group(self._experiement_configurations)
        exp_group_count = len(exp_grouped.keys())
        count = 1
        for exp_files in exp_grouped.values():
            # base directory
            logging.info('Averaging group %d of %d', count, exp_group_count)
            count += 1

            first_exp = exp_files[0]
            base_path = self._get_base(self._get_base(first_exp[CONST_CONFIG]))
            conf_files = [exp[CONST_CONFIG] for exp in exp_files]

            analyzer = Analyzer(conf_files)
            if not os.path.exists(self._metrics(base_path)):
                os.makedirs(self._metrics(base_path))

            # routing choice stats
            with open(self._metrics(base_path, 'stats.json'), 'w') as s_file:
                routing_choice_avg, graph_data = analyzer.run_routing_choice_metrics()
                s_file.write(json.dumps(graph_data))

            r_metrics = analyzer.get_routing_metrics(None, None, None)
            r_metrics.calculate_metrics()
            self._write_analysis_data(base_path, r_metrics)


    def _get_experiments_by_group(self, experiments):
        by_groups = {}
        for exp in experiments:
            if exp[CONST_GROUP] not in by_groups:
                by_groups[exp[CONST_GROUP]] = []
            by_groups[exp[CONST_GROUP]].append(exp)
        return by_groups

    def _write_analysis_data(self, base_path, r_metrics):
        # path length
        with open(self._metrics(base_path, 'path_histo.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_path_lengths()))
        # anon metrics
        with open(self._metrics(base_path, 'sender_set_size.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_sender_set()))

        with open(self._metrics(base_path, 'sender_set_size_by_hop.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_sender_set_by_hop()))
        # entropy metrics
        with open(self._metrics(base_path, 'entropy.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_entropy()))
        with open(self._metrics(base_path, 'entropy_normalized.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_entropy_normalized()))

        with open(self._metrics(base_path, 'entropy_by_hop.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_entropy_by_hop()))
        with open(self._metrics(base_path, 'entropy_normalized_by_hop.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_entropy_normalized_by_hop()))

        with open(self._metrics(base_path, 'top_rank_set_size_by_hop.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_top_rank_set_size_by_hop()))

        with open(self._metrics(base_path, 'top_rank_by_hop.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_top_rank_by_hop()))
        # entropy metric using actual backoff
        with open(self._metrics(base_path, 'entropy_actual.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_entropy_actual()))
        with open(self._metrics(base_path, 'entropy_normalized_actual.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_entropy_normalized_actual()))

        with open(self._metrics(base_path, 'entropy_by_hop_actual.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_entropy_by_hop_actual()))
        with open(self._metrics(base_path, 'entropy_normalized_by_hop_actual.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_entropy_normalized_by_hop_actual()))

        # consolidated metrics
        with open(self._metrics(base_path, 'consolidated.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.get_summary()))
        # intercept hop
        with open(self._metrics(base_path, 'intercept.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_intercept_hop()))
        with open(self._metrics(base_path, 'intercept_percent.json'), 'w') as g_file:
            g_file.write(json.dumps(r_metrics.graph_intercept_percent_hop()))
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
