# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Unit test for routing tree
'''
import unittest

from lib.utils import distance


class TestUtilities(unittest.TestCase):
    '''
    Test utility functions
    '''

    def test_distance(self):
        # issues with values represented as floats was causing issues when comparing distance
        d_1 = distance(0.99, 0.05)
        d_2 = distance(0.11, 0.05)
        self.assertTrue(d_1 == 0.06)
        self.assertTrue(d_2 == d_1)
