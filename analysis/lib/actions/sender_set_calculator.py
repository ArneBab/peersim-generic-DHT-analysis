# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Calculate the send set for each captured route
'''
import os
import json
import logging
from lib.utils import distance, timeit
from lib.routing.tree import RoutingTree
from lib.actions.metric_base import MetricBase
from lib.routing.route_prediction import rank_greedy, rank_greedy_2_hop


class SenderSetCalculator(MetricBase):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self, graph_manager, experiment_config, routing_choice):
        super(SenderSetCalculator, self).__init__()
        self.graph_manager = graph_manager
        self.experiment_config = experiment_config
        self.routing_choice = routing_choice
        self.output_file_path = ''
        self.output_file = None

    def get_output_file_path(self):
        '''
        Start of processing a new file
        :return: Path to the output file
        '''
        return self.output_file_path

    def on_start(self, file_path):
        '''
        Start of processing a new file
        :param file_path: Full path to the file being processed
        '''
        super(SenderSetCalculator, self).on_start(file_path)
        directory = os.path.dirname(file_path)
        self.output_file_path = os.path.join(
            directory, 'sender_set.routing.json')
        self.output_file = open(self.output_file_path, 'w')

    def on_stop(self):
        '''
        End of processing a new file
        '''
        super(SenderSetCalculator, self).on_stop()
        if self.output_file is not None:
            self.output_file.close()
        self.output_file = None

    #@timeit
    def process(self, data_object):
        '''
        Process a given file
        :param data_object: JSON object
        :return: Updated data_object reference
        '''
        super(SenderSetCalculator, self).process(data_object)
        nx_graph = self.graph_manager.get_graph(data_object['cycle'])

        # calculate soure and destination difference
        source_node = nx_graph.node[data_object['source_node']]
        destination_node = nx_graph.node[data_object['destination_node']]
        x_loc = source_node['location']
        y_loc = destination_node['location']
        data_object['distance'] = distance(x_loc, y_loc)

        # calculate the anonymity set metrics
        a_node, p_node = next(
            iter(self._get_adversaries(data_object)), (None, None))
        if a_node is None:
            # no adversary node found in the path
            self.output_file.write(json.dumps(data_object))
            self.output_file.write('\n')
            return data_object

        # map routing type to ranking algorithm
        router_type = self.experiment_config.get_parameter('router_type')
        look_ahead = self.experiment_config.get_parameter('look_ahead')
        route_alg = None
        if router_type == 'DHTRouterGreedy':
            if int(look_ahead) == 1:
                route_alg = rank_greedy
            elif int(look_ahead) == 2:
                route_alg = rank_greedy_2_hop
            else:
                raise Exception('Unknown number of look ahead')
        else:
            raise Exception('Unknown routing type')

        # calculate sender set and preferred routes
        logging.info('Hop : %d', a_node['hop'])
        r_tree = RoutingTree(nx_graph, route_alg, max_length=20)
        if r_tree.build(a_node['id'], p_node['id'],
                        a_node['hop'], data_object['target']):

            a_data = {'calculated': True, 'hop': a_node['hop']}
            a_data['tree'] = r_tree.to_bracket()
            a_data['ranked_set'] = r_tree.get_sender_set_rank()
            a_data['probability_set_top_rank'] = r_tree.get_sender_set_distribution_by_top_rank()
            a_data['probability_set'] = r_tree.get_sender_set_distribution(
                r_tree.distro_rank_exponetial_backoff)

            a_set = r_tree.get_sender_set()
            a_data['full_set'] = {'length': len(a_set), 'nodes': a_set}
            a_data['probability_set_sender_set'] = r_tree.get_sender_set_distribution_full()

            # calculate the probability distribution using the actual routing choices
            routing_choice_avg = self.routing_choice.get_final_routing_choices()
            largest_rank = sorted(routing_choice_avg.keys())[-1]

            def _distro_rank(rank):
                if rank > largest_rank or routing_choice_avg[rank] == 0.0:
                    return (routing_choice_avg[largest_rank] / (2 * (rank - largest_rank))) / 100.0
                return routing_choice_avg[rank] / 100.0
            a_data['probability_set_actual'] = r_tree.get_sender_set_distribution(
                _distro_rank)
        else:
            a_data = {'calculated': False, 'hop': a_node['hop']}

        data_object['anonymity_set'] = a_data

        self.output_file.write(json.dumps(data_object))
        self.output_file.write('\n')
        return data_object

    def _get_adversaries(self, data_obj):
        adversaries = []
        previous_node = None
        for node in data_obj['routing_path']['path']:
            if node['is_adversary']:
                if previous_node is None:
                    raise Exception(
                        'adversary cannot be the source node: %s', str(node))
                adversaries.append((node, previous_node))
            previous_node = node
        return adversaries
