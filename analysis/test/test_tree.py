# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Unit test for routing tree
'''
import unittest

from lib.tree import RoutingTree
from .utils import get_nx_graphs, list_equals


class TestTree(unittest.TestCase):
    '''
    Test the RoutingTree Class
    '''

    def test_too_much_work(self):
        tree = RoutingTree()
        nx_graph = get_nx_graphs()[0]
        self.assertFalse(tree.build(nx_graph, 6, 7, 5))
        self.assertTrue(tree.build(nx_graph, 6, 7, 5, False))

    def test_works(self):
        tree = RoutingTree()
        nx_graph = get_nx_graphs()[0]
        self.assertTrue(tree.build(nx_graph, 6, 7, 5, False))
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

        self.assertTrue(tree.get_count() == 28)

        self.assertTrue(list_equals(
            [0, 3, 2, 11, 13, 9, 12, 8], tree.get_sender_set()))

    def test_distro_rank_greedy(self):
        tree = RoutingTree()
        nx_graph = get_nx_graphs()[0]
        self.assertTrue(tree.build(nx_graph, 13, 5, 4, False))
        self.assertTrue(tree.get_height() == 5)
        distro = tree.get_sender_set_distribution(
            tree.rank_greedy, tree.distro_rank_exponetial_backoff,
            0.29)

        self.assertTrue(round(distro[0], 3) == 0.051)
        self.assertTrue(round(distro[1], 3) == 0.026)
        self.assertTrue(round(distro[2], 3) == 0.218)
        self.assertTrue(round(distro[6], 3) == 0.013)
        self.assertTrue(round(distro[7], 3) == 0.103)
        self.assertTrue(round(distro[8], 3) == 0.205)
        self.assertTrue(round(distro[9], 3) == 0.103)
        self.assertTrue(round(distro[10], 3) == 0.026)
        self.assertTrue(round(distro[12], 3) == 0.256)

        ranked = tree.get_sender_set_rank(tree.rank_greedy, 0.29)

        self.assertTrue(list_equals([2, 12, 8], ranked[2]))
        self.assertTrue(list_equals([7, 9], ranked[4]))
        self.assertTrue(list_equals([12, 0], ranked[6]))
        self.assertTrue(list_equals([1, 10], ranked[8]))
        self.assertTrue(list_equals([6, 2], ranked[10]))

    def test_distro_rank_greedy_2(self):
        tree = RoutingTree()
        nx_graph = get_nx_graphs()[0]
        self.assertTrue(tree.build(nx_graph, 11, 3, 3, False))
        self.assertTrue(tree.get_height() == 4)
        distro = tree.get_sender_set_distribution(
            tree.rank_greedy, tree.distro_rank_exponetial_backoff,
            0.55)

        self.assertTrue(round(distro[0], 3) == 0.067)
        self.assertTrue(round(distro[5], 3) == 0.133)
        self.assertTrue(round(distro[2], 3) == 0.267)
        self.assertTrue(round(distro[6], 3) == 0.267)
        self.assertTrue(round(distro[10], 3) == 0.267)

    def test_out_of_bounds(self):
        tree = RoutingTree()
        with self.assertRaises(Exception):
            tree.get_data_at_level(0)
        with self.assertRaises(Exception):
            tree.get_data_at_level(-1)
        with self.assertRaises(Exception):
            tree.get_data_at_level(1)
