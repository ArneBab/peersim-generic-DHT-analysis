# -*- coding: utf-8 -*-
'''
Updated on August, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Generate configuration files for Peersim simulator
'''
import logging
import os
from random import randint
from string import Template

import networkx as nx
from topology_generator import TopologyGenerator

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

    #'topology_type', 'router_type', 'look_ahead', 'adversary_count', 'size', 'degree', 'repeat'
    _variables = dict(
        random_seed=lambda x: str(randint(1, 1000000)),
        experiment_count=['1'],
        size=[100, 200, 300, 400],
        degree=[4, 5, 6],
        repeat=[1, 2],
        look_ahead=[1, 2],
        adversary_count=['1%'],
        traffic_step=[1000],
        #size=[500, 1000, 2000, 3000, 4000, 5000],
        #degree=[6, 8, 10, 12, 14],
        #repeat=[1, 2, 3, 4],
        #look_ahead=[1, 2],
        #adversary_count=['1', '1%', '2%', '3%'],
        #traffic_step=[50],
        traffic_generator=['RandomPingTraffic'],
        topology_type=['random', 'random_erdos_renyi', 'random_power_law', 'small_world', 'structured'],
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

    def build_configs(self):
        '''
        Build the topologies for each permutation
        '''
        self.reset()
        total = len(self._permutations)
        for perm_index in range(0, total):
            logging.info('Generating topology %d of %d' % (perm_index+1, total))
            config = self._permutations[perm_index]
            self._eval_topology_type(config)

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
        self._state_iterator = self._state_iterator + 1
        return self._state_iterator < len(self._permutations)

    def get_total_count(self):
        return len(self._permutations)

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

        # special check for topology type
        #self._eval_topology_type(config)

        return config

    def _eval_topology_type(self, config):

        path = os.path.join(Configuration.file_path_for_config(
            config), 'input-graph.gml')

        # check if directory exists
        dir_name = os.path.dirname(path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        def is_float(s):
            try:
                return float(s)
            except ValueError:
                return None

        if os.path.exists(path):
            logging.info('Topology already exists ... skipping')
        else:
            size = int(config['size'])
            degree = int(config['degree'])

            if config['topology_type'] == 'random':
                graph = TopologyGenerator.generate_random_topology(
                    size, degree)
            elif config['topology_type'] == 'random_erdos_renyi':
                graph = TopologyGenerator.generate_random_topology_erdos_renyi(size, degree)
            elif config['topology_type'] == 'random_power_law':
                graph = TopologyGenerator.generate_random_power_law_topology(size, degree)
            elif config['topology_type'] == 'small_world':
                graph = TopologyGenerator.generate_small_world_topology(size, degree)
            elif config['topology_type'] == 'structured':
                graph = TopologyGenerator.generate_structured_topology(size, degree)
            else:
                raise Exception('Unknown topology type')
                
            with open(path, 'w') as g_file:
                for line in nx.generate_gml(graph):
                    # hack to fix mantissa on floats
                    if 'E-' in line:
                        components = line.split(' ')
                        for i in range(0, len(components)):
                            value = is_float(components[i])
                            if value:
                                components[i] = '{:.18f}'.format(value)
                        line = ' '.join(components)
                    g_file.write((line + '\n').encode('ascii'))

        config['topology_file'] = path

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
        return ['topology_type', 'router_type', 'look_ahead', 'adversary_count', 'size', 'degree', 'repeat']

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

    @staticmethod
    def get_hash(config, excluded=[]):
        '''
        Get a hash of the used variables
        '''
        return hash(Configuration.get_hash_name(config, excluded))

    @staticmethod
    def get_hash_name(config, excluded=[]):
        '''
        Get a hash of the used variables as a string
        '''
        identity = ''
        for param in Configuration.get_parameters():
            if param in excluded:
                continue
            if param not in config:
                continue
            if 'value' in config[param]:
                identity += ':' + str(config[param]['value'])
            else:
                identity += ':' + str(config[param])
        return identity

    @staticmethod
    def get_group_hash(config):
        '''
        Get a hash value for the config group
        i.e. all experimenents that have the same variables execpt the repeat components
        '''
        return Configuration.get_hash(config, ['repeat'])
