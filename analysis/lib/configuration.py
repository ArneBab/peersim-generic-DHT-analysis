# -*- coding: utf-8 -*-
'''
Updated on August, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Generate configuration files for Peersim simulator
'''
import os
from random import randint
from string import Template

ROUTING_DATA_FILE_NAME = 'routing.json'
GRAPH_DATA_PATH = 'graphs'


class Configuration(object):
    '''
    Enumerates simulation parameters and generates corresponding Peersim simulation
    configuration files.
    '''

    _template_string = ''
    _permutations = None
    _state_iterator = None
    _output_directory = ''

    _variables = dict(
        random_seed=lambda x: str(randint(1, 1000000)),
        experiment_count='1',
        size=[100],
        #size=[10, 100, 1000],
        repeat=[1],
        # repeat=[1,2,3,4,5,6,7,8,9,10],
        look_ahead=[2],
        # adversary_count=[1, 1%, 2%],
        adversary_count=[1],
        traffic_generator='RandomPingTraffic',
        router_type=['DHTRouterGreedy'],
        router_can_backtrack=['true'],
        router_drop_rate=[0.0],
        router_loop_detection=['GUIDLoopDetection'],
        router_randomness=[0.0],
        routing_data_path=lambda x: os.path.join(
            Configuration.file_path_for_config(x), ROUTING_DATA_FILE_NAME),
        graph_data_path=lambda x: os.path.join(
            Configuration.file_path_for_config(x), GRAPH_DATA_PATH),
        path=lambda x: Configuration.file_path_for_config(x, '')
    )

    def __init__(self, output_directory='', template_file_name=None):
        self._output_directory = output_directory
        # get the default template file
        if template_file_name is None:
            template_file_name = os.path.join(os.path.dirname(
                os.path.realpath(__file__)), '../resources/template.cfg')

        with open(template_file_name, 'r') as template_file:
            self._template_string = template_file.read()

    def get_file_path(self):
        '''
        Get the path path for the current configuration
        '''
        return Configuration.file_path_for_config(self._permutations[self._state_iterator])

    def generate_experiement_config(self):
        '''
        Get the current configuration as a string
        '''
        template_engine = Template(self._template_string)
        return template_engine.substitute(self._permutations[self._state_iterator])

    def get_config(self):
        '''
        Get the dict of the current settings
        '''
        return self._permutations[self._state_iterator]

    def next(self):
        '''
        Moves the configuration iterator to the next configuration
        '''
        if self._state_iterator is None:
            self.reset()
        self._state_iterator = self._state_iterator + 1
        return self._state_iterator < len(self._permutations)

    def reset(self):
        '''
        Reset the iterator to tbe beginning of the variable combinations,
        and generate all the permutations.
        '''
        self._state_iterator = -1
        self._permutations = []
        self._generate_permutations(self._variables.keys(), 0, dict())

    def _generate_permutations(self, variable_list, current_index, current_config):
        variable = variable_list[current_index]
        options = self._variables[variable]

        if isinstance(options, list):  # list of values
            for value in options:
                current_config[variable] = value
                if current_index == (len(variable_list) - 1):
                    self._permutations.append(
                        self._evaluate_config(current_config))
                    continue  # stopping condition
                self._generate_permutations(
                    variable_list, current_index + 1, current_config)
        else:  # single value
            current_config[variable] = options
            if current_index == (len(variable_list) - 1):
                self._permutations.append(
                    self._evaluate_config(current_config))
                return  # stop condition
            self._generate_permutations(
                variable_list, current_index + 1, current_config)

    def _evaluate_config(self, current_config):
        config = current_config.copy()
        # set output directory variable
        config['output_base_directory'] = self._output_directory

        for (key, value) in current_config.items():
            if callable(value):
                config[key] = value(config)
            else:
                config[key] = str(value)
        return config

    def __getitem__(self, key):
        '''
        Get the current value of a given configuration parameter
        :param key: parameter name
        :return: Value assigned to the configuration parameter
        '''
        if not self._permutations[self._state_iterator].has_key(key):
            raise Exception('No such configuration member found')
        return self._permutations[self._state_iterator][key]

    def __setitem__(self, key, value):
        '''
        Set the current value of a given configuration parameter
        :param key: parameter name
        :param value: value to assign to the parameter
        '''
        if not self._permutations[self._state_iterator].has_key(key):
            raise Exception('No such configuration member found')
        self._permutations[self._state_iterator][key] = value

    @staticmethod
    def get_parameters():
        '''
        Get the used experiment parameters
        :return: List of parameter names
        '''
        return ['router_type', 'look_ahead', 'adversary_count', 'size', 'repeat']

    @staticmethod
    def file_path_for_config(config, output_base_directory=None):
        '''
        Generate a file path for storing data related to the given configuration
        :param config: Dictionary of the configuration values
        :return: relative file path
        '''
        path = config['output_base_directory']
        if output_base_directory is not None:
            path = output_base_directory
        for key in Configuration.get_parameters():
            path = os.path.join(path, str(key), str(config[key]))
        return path
