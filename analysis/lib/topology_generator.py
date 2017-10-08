# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Generate experiment topologies
'''
import random
import networkx as nx


class TopologyGenerator(object):
    '''
    Class the handles all the topology generation
    '''

    @staticmethod
    def generate_random_topology(size, average_degree):
        graph = nx.random_regular_graph(average_degree, size)
        for node_id in graph.nodes():
            loc = random.random()
            graph.node[node_id]['label'] = str(loc)
            graph.node[node_id]['location'] = loc
        return graph
