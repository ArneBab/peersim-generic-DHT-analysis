# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Unit test for routing metrics
'''
import unittest
import tempfile

from lib.routing_metrics import RoutingMetrics
from .utils import get_nx_graphs_100, get_nx_graphs, list_equals
from .utils import get_route_json_path, get_route_json_path_100


class TestRoutingMetrics(unittest.TestCase):
    '''
    Test the RoutingMetrics Class
    '''

    def test_works(self):
        with tempfile.NamedTemporaryFile() as output_file:
            r_metric = RoutingMetrics(
                get_nx_graphs_100(), get_route_json_path_100(), output_file.name, {})
            r_metric.calculate_metrics()
            r_data = r_metric.graph_path_lengths()
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

    def test_metrics(self):
        with tempfile.NamedTemporaryFile() as output_file:
            r_metric = RoutingMetrics(
                get_nx_graphs(), get_route_json_path(), output_file.name, {})
            r_metric.calculate_metrics()
            r_data = r_metric.graph_metrics()
        degrees = r_data['data'][0]
        diameters = r_data['data'][1]
        self.assertTrue(len(degrees) == 1)
        self.assertTrue(round(degrees[0], 2) == 3.57)
        self.assertTrue(diameters[0] == 4)

    def test_missing_file(self):
        with self.assertRaises(Exception):
            RoutingMetrics(
                get_nx_graphs(), '/tmp/junk/dfa/dfadf.json', '/tmp/junk/dfa/dfadf2.json', {})
