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
from lib.topology_generator import TopologyGenerator as TopGen

ROUTING_DATA_FILE_NAME = 'routing.json'
GRAPH_DATA_PATH = 'graphs'


class Configuration(object):
    '''
    Enumerates simulation parameters and generates corresponding Peersim simulation
    configuration files.
    '''

    @staticmethod
    def file_path_for_config(config, output_base_directory=None):
        '''
        Generate a file path for storing data related to the given configuration
        :param config: Dictionary of the configuration values
        :return: relative file path
        '''
        # needs to be before _variables or pylint complains
        path = config['output_base_directory']
        if output_base_directory is not None:
            path = output_base_directory
        path = os.path.join(path,
                            str(Configuration.get_group_hash(config)),
                            str(config['repeat']))
        return path

    _variables = dict(
        random_seed=lambda x: str(randint(1, 1000000)),
        experiment_count=['1'],
        size=[1000, 2000, 3000, 4000],
        degree=[8, 10, 12, 14],
        repeat=[1, 2, 3],
        look_ahead=[1, 2],
        #adversary_count=['1%', '2%'],
        adversary_count=['1%'],
        traffic_step=[500],
        traffic_generator=['RandomPingTraffic'],
        topology_type=['random_erdos_renyi', 'small_world', 'structured'],
        router_type=['DHTRouterGreedy'],
        router_can_backtrack=['true'],
        router_drop_rate=[0.0],
        router_loop_detection=['GUIDLoopDetection', 'NoLoopDetection'],
        router_randomness=[0.0, 0.05, 0.1],
        routing_data_path=lambda x: os.path.join(
            Configuration.file_path_for_config(x, ''), ROUTING_DATA_FILE_NAME),
        graph_data_path=lambda x: os.path.join(
            Configuration.file_path_for_config(x, ''), GRAPH_DATA_PATH),
        path=lambda x: Configuration.file_path_for_config(x, ''),
        name=lambda x: Configuration.get_hash_name(x),
        group_name=lambda x: Configuration.get_group_hash_name(x)
    )

    _top_gen_map = {'random': TopGen.generate_random_topology,
                    'random_erdos_renyi': TopGen.generate_random_topology_erdos_renyi,
                    'random_power_law': TopGen.generate_random_power_law_topology,
                    'small_world': TopGen.generate_small_world_topology,
                    'structured': TopGen.generate_structured_topology
                    }

    def __init__(self, output_directory='', template_file_name=None):
        self._permutations = None
        self._state_iterator = None
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
        # generate topology if needed
        not_at_end = self._state_iterator < len(self._permutations)
        if not_at_end:
            self._eval_topology_type(self._permutations[self._state_iterator])
        return not_at_end

    def get_total_count(self):
        '''
        Get the total number of experiment configurations
        :return: int count of experiment configurations
        '''
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

        return config

    def _eval_topology_type(self, config):

        path = os.path.join(Configuration.file_path_for_config(
            config), 'input-graph.gml')
        rel_path = os.path.join(Configuration.file_path_for_config(
            config, ''), 'input-graph.gml')
        exp_archived = os.path.join(Configuration.file_path_for_config(
            config), 'archive.zip')

        # check if directory exists
        dir_name = os.path.dirname(path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        def _is_float(s):
            try:
                return float(s)
            except ValueError:
                return None

        # check if the file was already generated
        config['topology_file'] = rel_path
        if os.path.exists(path):
            return

        if os.path.exists(exp_archived):
            return

        logging.info('Generating topology file ...')
        size = int(config['size'])
        degree = int(config['degree'])
        top_type = config['topology_type']
        if top_type not in self._top_gen_map:
            raise Exception('Unknown topology type')

        graph = self._top_gen_map[top_type](size, degree)

        with open(path, 'w') as g_file:
            for line in nx.generate_gml(graph):
                # hack to fix mantissa on floats
                if 'E-' in line:
                    components = line.split(' ')
                    for i in range(0, len(components)):
                        value = _is_float(components[i])
                        if value:
                            components[i] = '{:.18f}'.format(value)
                    line = ' '.join(components)
                g_file.write((line + '\n').encode('ascii'))

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
        return ['topology_type', 'router_type', 'router_randomness',
                'look_ahead', 'adversary_count', 'router_loop_detection', 'size', 'degree', 'repeat']

    @staticmethod
    def get_hash(config, excluded=[]):
        '''
        Get a hash of the used variables
        '''
        return hash(Configuration.get_hash_name(config, excluded))

    @staticmethod
    def get_group_hash_name(config):
        """Get the hash name for the group

        Arguments:
            config {dict} -- Configuration dictionary

        Returns:
            str -- String representation of the group
        """

        return Configuration.get_hash_name(config, ['repeat'])

    @staticmethod
    def get_hash_name(config, excluded=[]):
        '''
        Get a hash of the used variables as a string
        '''
        identity = ''
        for param in Configuration.get_parameters():
            if param in excluded:
                identity += ':'
                continue
            if param not in config:
                identity += ':'
                continue
            value = str(config[param]).lower()

            value = value.replace('loopdetection', '').replace(
                'random_erdos_renyi', 'erdos')
            value = value.replace('small_world', 'small').replace(
                'structured', 'struc')
            value = value.replace('dhtrouter', '').replace('random', 'r_')

            identity += ':' + value
        return identity

    @staticmethod
    def get_group_hash(config):
        '''
        Get a hash value for the config group
        i.e. all experimenents that have the same variables execpt the repeat components
        '''
        return Configuration.get_hash(config, ['repeat'])
