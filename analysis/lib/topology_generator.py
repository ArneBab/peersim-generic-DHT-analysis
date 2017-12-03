# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Generate experiment topologies
'''
import logging
import math
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

    @staticmethod
    def generate_random_topology_erdos_renyi(size, average_degree):
        # https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93R%C3%A9nyi_model
        # http://homepage.divms.uiowa.edu/~sriram/196/spring12/lectureNotes/Lecture4.pdf

        # need to estimate p
        # degree = (n-1)p
        # p = degree/(n-1)
        connection_p = average_degree / (size - 1.0)
        graph = nx.gnp_random_graph(size, connection_p)
        for node_id in graph.nodes():
            loc = random.random()
            graph.node[node_id]['label'] = str(loc)
            graph.node[node_id]['location'] = loc

            # don't let the graph have orphans
            if len(graph[node_id]) < 1:
                # add a random connection
                rand_index = random.randint(0, size-1)
                graph.add_edge(node_id, rand_index)

        # check if the graph is connected
        # if not try generating the graph again
        if not nx.is_connected(graph):
            logging.info('Graph not connected: Regenerating ...')
            return TopologyGenerator.generate_random_topology_erdos_renyi(size, average_degree)

        return graph

    @staticmethod
    def generate_random_power_law_topology(size, average_degree):
        # https://networkx.github.io/documentation/latest/reference/generated/networkx.generators.random_graphs.powerlaw_cluster_graph.html#networkx.generators.random_graphs.powerlaw_cluster_graph

        graph = nx.powerlaw_cluster_graph(size, average_degree, 0.2)
        for node_id in graph.nodes():
            loc = random.random()
            graph.node[node_id]['label'] = str(loc)
            graph.node[node_id]['location'] = loc

            # don't let the graph have orphans
            if len(graph[node_id]) < 1:
                # add a random connection
                rand_index = random.randint(0, size-1)
                graph.add_edge(node_id, rand_index)

        # check if the graph is connected
        # if not try generating the graph again
        if not nx.is_connected(graph):
            logging.info('Graph not connected: Regenerating ...')
            return TopologyGenerator.generate_random_power_law_topology(size, average_degree)

        return graph

    @staticmethod
    def generate_small_world_topology(size, average_degree):
        connection_p = 0.4
        try:
            graph = nx.connected_watts_strogatz_graph(size, average_degree, connection_p)
        except nx.NetworkXError:
            logging.info('Graph not connected: Regenerating ...')
            return TopologyGenerator.generate_small_world_topology(size, average_degree)

        # add labels. Need to add labels in order
        label_step = 1.0 / size
        current_label = 0.0
        for node_id in graph.nodes():
            graph.node[node_id]['label'] = str(current_label)
            graph.node[node_id]['location'] = current_label
            current_label += label_step

        return graph

    @staticmethod
    def generate_structured_topology(size, average_degree):
        graph = nx.Graph()
        graph.add_nodes_from(range(size))

        # add labels. Need to add labels in order
        label_step = 1.0 / size
        current_label = 0.0
        for node_id in graph.nodes():
            graph.node[node_id]['label'] = str(current_label)
            graph.node[node_id]['location'] = current_label
            current_label += label_step

        # create ring
        nodes_1 = range(size)
        nodes_2 = nodes_1[1:] + [0]
        graph.add_edges_from(zip(nodes_1, nodes_2))
        # each node has degree 2 now

        def add_link(graph, exp):
            # we assume the nodes are labeled 0 thru (n-1)
            # and the nodes are already in ascending order
            size = graph.number_of_nodes()
            placement = int(math.ceil(size / float(exp)))
            # placement needs to be greater than 2 or the graph is already connected
            if placement < 2:
                return False
            nodes_1 = range(size)
            nodes_2 = [(i + placement) % size for i in nodes_1]
            graph.add_edges_from(zip(nodes_1, nodes_2))
            return True

        # now bring the graph degree as close to average degree as we can
        exp = 1
        while len(graph.edge[0]) < average_degree:
            exp = exp * 2
            if not add_link(graph, exp):
                break
        graph.graph['invariant'] = exp
        return graph
