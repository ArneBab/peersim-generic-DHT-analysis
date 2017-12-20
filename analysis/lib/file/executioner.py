# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Code for executing simulation experiments
'''
import os
import logging
import subprocess

STD_OUT_FILE_NAME = 'stdout.txt'


class Executioner(object):
    '''
    Class for executing simulations
    '''

    _java_path = None

    def __init__(self, exe_path):
        self._java_path = os.path.pathsep.join([os.path.abspath(os.path.join(exe_path, 'bin', '*')),
                                                os.path.abspath(os.path.join(exe_path, 'lib', '*'))])

    def run(self, experiment_config_file, base_directory):
        '''
        Run the simulation
        '''
        java_exe_template = ['java', '-cp',
                             self._java_path, 'peersim.Simulator']
        dir_path = os.path.dirname(experiment_config_file)
        with open(os.path.join(dir_path, STD_OUT_FILE_NAME), 'w') as std_out_file:
            command = list(java_exe_template)
            command.append(experiment_config_file)
            logging.debug('Running command: %s', ' '.join(command))
            return subprocess.call(command, cwd=base_directory,
                                   stdout=std_out_file, stderr=std_out_file)
