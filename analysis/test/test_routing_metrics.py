# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Unit test for routing metrics
'''
import unittest

from lib.routingMetrics import RoutingMetrics
from .utils import get_nx_graph, get_route_json_path, list_equals


class TestRoutingMetrics(unittest.TestCase):
    '''
    Test the RoutingMetrics Class
    '''

    def test_works(self):
        r_metric = RoutingMetrics([get_nx_graph()], get_route_json_path())
        r_data = r_metric.get_path_length_graph_data()
        r_path_lengths = r_data['data'][0]
        c_path_lengths = r_data['data'][1]
        expected_r = [0 for i in range(1, 100)]
        expected_c = expected_r[:]

        expected_r[24 - 1] = 1
        expected_r[27 - 1] = 1
        expected_r[32 - 1] = 1
        expected_r[33 - 1] = 1
        expected_r[57 - 1] = 1
        expected_r[99 - 1] = 1

        expected_c[24 - 1] = 2
        expected_c[27 - 1] = 2
        expected_c[57 - 1] = 2

        self.assertTrue(list_equals(expected_r, r_path_lengths))
        self.assertTrue(list_equals(expected_c, c_path_lengths))

    def test_missing_file(self):
        with self.assertRaises(Exception):
            RoutingMetrics([get_nx_graph()], '/tmp/junk/dfa/dfadf.json')
