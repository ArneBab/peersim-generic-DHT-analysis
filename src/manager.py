# -*- coding: utf-8 -*-
'''
Updated on August, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Main class for running experiments and anaylzing results
'''
import logging
import argparse
import os
import subprocess
from lib.configuration import Configuration


class Manager(object):

    _experiement_configurations = []

    def main(self, args):
        logging.info('Starting ...')

        # generate experiment configurations first
        config_manager = Configuration(args.d)
        while(config_manager.next()):
            file_name = os.path.join(
                args.d, config_manager.get_file_path(), 'config.cfg')
            file_name = os.path.abspath(file_name)
            dir_name = os.path.dirname(file_name)

            # check if directory exists
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)

            with open(file_name, 'w') as c_file:
                c_file.write(config_manager.generate_config())
                self._experiement_configurations.append(file_name)
        logging.info('Generated %s experiment configurations' %
                     len(self._experiement_configurations))

        self.run_experiments(args)

    def run_experiments(self, args):
        # run each of the experiments
        java_paths = ':'.join([os.path.abspath(os.path.join(args.p, 'bin', '*')),
                               os.path.abspath(os.path.join(args.p, 'lib', '*'))])
        java_exe_template = ['java', '-cp', java_paths, 'peersim.Simulator']

        experiment_count = 1
        for experiment_file in self._experiement_configurations:
            dir_path = os.path.dirname(experiment_file)
            with open(os.path.join(dir_path, 'stdout.txt'), 'w') as std_out_file:
                command = list(java_exe_template)
                command.append(experiment_file)
                logging.info('Running command %d of %d' % (
                    experiment_count, len(self._experiement_configurations)))
                logging.debug('Running command: %s' % ' '.join(command))
                exit_code = subprocess.call(
                    command, stdout=std_out_file, stderr=std_out_file)
                if exit_code > 0:
                    logging.error('Returned exit code %d' % exit_code)
                experiment_count = experiment_count + 1


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    parser = argparse.ArgumentParser(
        description='Run some Anonymous P2P DHT experiments.')
    parser.add_argument('-d', default='.', type=str,
                        help='Directory to store output in')
    parser.add_argument('-p', default='.', type=str,
                        help='Directory to find the PeerSim binaries in')
    Manager().main(parser.parse_args())
