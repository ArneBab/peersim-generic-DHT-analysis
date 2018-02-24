# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Unit test for routing tree
'''
import unittest

from lib.routing.tree import RoutingTree
from lib.routing.route_prediction import rank_greedy, rank_greedy_2_hop
from .utils import get_nx_graphs, get_nx_graphs_100, list_equals, get_nx_graphs_100_structured


class TestTree(unittest.TestCase):
    '''
    Test the RoutingTree Class
    '''

    def test_structured_prediction(self):
        nx_graph = get_nx_graphs_100_structured()[0]
        tree = RoutingTree(nx_graph, rank_greedy)
        tree.build(105, 104, 8, .05)
        
        self.assertTrue(tree.get_height() == 9)
        ranked = tree.get_sender_set_rank()
        self.assertTrue(162 in ranked[8])


    def test_works(self):
        nx_graph = get_nx_graphs()[0]
        tree = RoutingTree(nx_graph, rank_greedy)
        tree.build(6, 7, 5, .5)

        self.assertTrue(tree.get_height() == 6)
        level_0 = tree.get_data_at_level(0)
        level_1 = tree.get_data_at_level(1)
        level_2 = tree.get_data_at_level(-2)
        level_3 = tree.get_data_at_level(3)
        level_4 = tree.get_data_at_level(4)
        level_5 = tree.get_data_at_level(5)
        with self.assertRaises(Exception):
            tree.get_data_at_level(6)

        self.assertTrue(list_equals([6], level_0))
        self.assertTrue(list_equals([7], level_1))
        self.assertTrue(list_equals([4], level_2))
        self.assertTrue(list_equals([5, 10, 1], level_3))
        self.assertTrue(list_equals([13, 9], level_4))
        self.assertTrue(list_equals([0], level_5))

        self.assertTrue(list_equals(
            [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13], tree.get_sender_set()))

    def test_distro_rank_greedy(self):
        nx_graph = get_nx_graphs()[0]
        tree = RoutingTree(nx_graph, rank_greedy)

        tree.build(13, 5, 4, 0.29)
        self.assertTrue(tree.get_height() == 5)
        distro = tree.get_sender_set_distribution(
            tree.distro_rank_exponetial_backoff)

        self.assertTrue(round(distro[0], 3) == 0.0)
        self.assertTrue(round(distro[1], 3) == 0.0)
        self.assertTrue(round(distro[2], 3) == 0.333)
        self.assertTrue(round(distro[6], 3) == 0.0)
        self.assertTrue(round(distro[7], 3) == 0.0)
        self.assertTrue(round(distro[8], 3) == 0.333)
        self.assertTrue(round(distro[9], 3) == 0.0)
        self.assertTrue(round(distro[10], 3) == 0.0)
        self.assertTrue(round(distro[12], 3) == 0.333)

        self.assertTrue(len(distro) == 11)

        ranked = tree.get_sender_set_rank()

        self.assertTrue(list_equals([2, 12, 8], ranked[5]))

    def test_distro_rank_greedy_2(self):
        nx_graph = get_nx_graphs()[0]
        tree = RoutingTree(nx_graph, rank_greedy)

        tree.build(11, 3, 3, 0.55)
        self.assertTrue(tree.get_height() == 4)
        distro = tree.get_sender_set_distribution(
            tree.distro_rank_exponetial_backoff)

        self.assertTrue(round(distro[0], 3) == 0.0)
        self.assertTrue(round(distro[5], 3) == 0.0)
        self.assertTrue(round(distro[2], 3) == 0.333)
        self.assertTrue(round(distro[6], 3) == 0.333)
        self.assertTrue(round(distro[10], 3) == 0.333)

    def test_out_of_bounds(self):
        nx_graph = get_nx_graphs()[0]
        tree = RoutingTree(nx_graph, None)
        with self.assertRaises(Exception):
            tree.get_data_at_level(0)
        with self.assertRaises(Exception):
            tree.get_data_at_level(-1)
        with self.assertRaises(Exception):
            tree.get_data_at_level(1)
