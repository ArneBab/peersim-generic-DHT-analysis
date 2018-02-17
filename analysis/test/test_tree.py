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
        tree = RoutingTree(nx_graph, rank_greedy, 1)
        tree.build(105, 104, 8, .05)
        
        self.assertTrue(tree.get_height() == 9)
        ranked = tree.get_sender_set_rank()
        self.assertTrue(162 in ranked[1])


    def test_works(self):
        nx_graph = get_nx_graphs()[0]
        tree = RoutingTree(nx_graph, rank_greedy, -1)
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
        self.assertTrue(list_equals([13, 12, 0, 1, 10, 9, 2], level_4))
        self.assertTrue(list_equals(
            [0, 3, 2, 3, 2, 11, 13, 9, 2, 12, 0, 8, 0, 12, 8], level_5))

        self.assertTrue(list_equals(
            [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13], tree.get_sender_set()))

    def test_distro_rank_greedy(self):
        nx_graph = get_nx_graphs()[0]
        tree = RoutingTree(nx_graph, rank_greedy, -1)

        tree.build(13, 5, 4, 0.29)
        self.assertTrue(tree.get_height() == 5)
        distro = tree.get_sender_set_distribution(
            tree.distro_rank_exponetial_backoff)

        self.assertTrue(round(distro[0], 3) == 0.051)
        self.assertTrue(round(distro[1], 3) == 0.026)
        self.assertTrue(round(distro[2], 3) == 0.218)
        self.assertTrue(round(distro[6], 3) == 0.013)
        self.assertTrue(round(distro[7], 3) == 0.103)
        self.assertTrue(round(distro[8], 3) == 0.205)
        self.assertTrue(round(distro[9], 3) == 0.103)
        self.assertTrue(round(distro[10], 3) == 0.026)
        self.assertTrue(round(distro[12], 3) == 0.256)

        self.assertTrue(len(distro) == 11)

        ranked = tree.get_sender_set_rank()

        self.assertTrue(list_equals([2, 12, 8], ranked[2]))
        self.assertTrue(list_equals([7, 9], ranked[4]))
        self.assertTrue(list_equals([12, 0], ranked[6]))
        self.assertTrue(list_equals([1, 10], ranked[8]))
        self.assertTrue(list_equals([6, 2], ranked[10]))

    def test_distro_rank_greedy_max_rank(self):
        nx_graph = get_nx_graphs()[0]
        tree = RoutingTree(nx_graph, rank_greedy, 2)

        tree.build(13, 5, 4, 0.29)
        self.assertTrue(tree.get_height() == 5)
        distro = tree.get_sender_set_distribution(
            tree.distro_rank_exponetial_backoff)

        self.assertTrue(round(distro[0], 3) == 0.0)
        self.assertTrue(round(distro[1], 3) == 0.0)
        self.assertTrue(round(distro[2], 3) == 0.25)
        self.assertTrue(round(distro[4], 3) == 0.0)
        self.assertTrue(round(distro[5], 3) == 0.0)
        self.assertTrue(round(distro[6], 3) == 0.0)
        self.assertTrue(round(distro[7], 3) == 0.125)
        self.assertTrue(round(distro[8], 3) == 0.25)
        self.assertTrue(round(distro[9], 3) == 0.125)
        self.assertTrue(round(distro[10], 3) == 0.0)
        self.assertTrue(round(distro[12], 3) == 0.25)

        self.assertTrue(len(distro) == 11)

        ranked = tree.get_sender_set_rank()

        self.assertTrue(list_equals([2, 12, 8], ranked[2]))
        self.assertTrue(list_equals([7, 9], ranked[4]))

        # reduce the max rank
        tree = RoutingTree(nx_graph, rank_greedy, 1)
        tree.build(13, 5, 4, 0.29)
        self.assertTrue(tree.get_height() == 5)
        distro = tree.get_sender_set_distribution(
            tree.distro_rank_exponetial_backoff)

        self.assertTrue(round(distro[0], 3) == 0.0)
        self.assertTrue(round(distro[1], 3) == 0.0)
        self.assertTrue(round(distro[2], 3) == 0.333)
        self.assertTrue(round(distro[4], 3) == 0.0)
        self.assertTrue(round(distro[5], 3) == 0.0)
        self.assertTrue(round(distro[6], 3) == 0.0)
        self.assertTrue(round(distro[7], 3) == 0.0)
        self.assertTrue(round(distro[8], 3) == 0.333)
        self.assertTrue(round(distro[9], 3) == 0.0)
        self.assertTrue(round(distro[10], 3) == 0.0)
        self.assertTrue(round(distro[12], 3) == 0.333)
        self.assertTrue(len(distro) == 11)

        ranked = tree.get_sender_set_rank()

        self.assertTrue(list_equals([2, 12, 8], ranked[2]))

    def test_distro_rank_greedy_2(self):
        nx_graph = get_nx_graphs()[0]
        tree = RoutingTree(nx_graph, rank_greedy, -1)

        tree.build(11, 3, 3, 0.55)
        self.assertTrue(tree.get_height() == 4)
        distro = tree.get_sender_set_distribution(
            tree.distro_rank_exponetial_backoff)

        self.assertTrue(round(distro[0], 3) == 0.067)
        self.assertTrue(round(distro[5], 3) == 0.133)
        self.assertTrue(round(distro[2], 3) == 0.267)
        self.assertTrue(round(distro[6], 3) == 0.267)
        self.assertTrue(round(distro[10], 3) == 0.267)

        tree = RoutingTree(nx_graph, rank_greedy_2_hop, -1)
        tree.build(11, 3, 3, 0.55)
        distro = tree.get_sender_set_distribution(
            tree.distro_rank_exponetial_backoff)

        self.assertTrue(round(distro[0], 3) == 0.111)
        self.assertTrue(round(distro[5], 3) == 0.222)
        self.assertTrue(round(distro[2], 3) == 0.222)
        self.assertTrue(round(distro[6], 3) == 0.222)
        self.assertTrue(round(distro[10], 3) == 0.222)

    def test_out_of_bounds(self):
        nx_graph = get_nx_graphs()[0]
        tree = RoutingTree(nx_graph, None)
        with self.assertRaises(Exception):
            tree.get_data_at_level(0)
        with self.assertRaises(Exception):
            tree.get_data_at_level(-1)
        with self.assertRaises(Exception):
            tree.get_data_at_level(1)
