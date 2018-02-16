# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Unit test for routing tree
'''
import unittest

from lib.topology_generator import TopologyGenerator


class TestTopology(unittest.TestCase):
    '''
    Test the Topology Generator Class
    '''

    def test_structured(self):
        graph = TopologyGenerator.generate_structured_topology(10, 3)
        self.assertTrue(graph.number_of_nodes() == 10)
        self.assertTrue(len(graph.adj[0]) == 3)
        self.assertTrue(graph.graph['invariant'] == 2)

        graph = TopologyGenerator.generate_structured_topology(10, 4)
        self.assertTrue(graph.number_of_nodes() == 10)
        self.assertTrue(len(graph.adj[0]) == 5)
        self.assertTrue(graph.graph['invariant'] == 4)

        graph = TopologyGenerator.generate_structured_topology(10, 5)
        self.assertTrue(graph.number_of_nodes() == 10)
        self.assertTrue(len(graph.adj[0]) == 5)
        self.assertTrue(graph.graph['invariant'] == 4)

        graph = TopologyGenerator.generate_structured_topology(10, 6)
        self.assertTrue(graph.number_of_nodes() == 10)
        self.assertTrue(len(graph.adj[0]) == 7)
        self.assertTrue(graph.graph['invariant'] == 8)


        graph = TopologyGenerator.generate_structured_topology(1000, 6)
        self.assertTrue(graph.number_of_nodes() == 1000)
        self.assertTrue(len(graph.adj[0]) == 7)
        self.assertTrue(graph.graph['invariant'] == 8)