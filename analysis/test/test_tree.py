# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Unit test for routing tree
'''
import unittest

from lib.tree import RoutingTree
from .utils import get_nx_graph, list_equals


class TestTree(unittest.TestCase):
    '''
    Test the RoutingTree Class
    '''

    def test_too_much_work(self):
        tree = RoutingTree()
        nx_graph = get_nx_graph()
        self.assertFalse(tree.build(nx_graph, 6, 7, 5))
        self.assertTrue(tree.build(nx_graph, 6, 7, 5, False))

    def test_works(self):
        tree = RoutingTree()
        nx_graph = get_nx_graph()
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

    def test_out_of_bounds(self):
        tree = RoutingTree()
        with self.assertRaises(Exception):
            tree.get_data_at_level(0)
        with self.assertRaises(Exception):
            tree.get_data_at_level(-1)
        with self.assertRaises(Exception):
            tree.get_data_at_level(1)
