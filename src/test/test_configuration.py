# -*- coding: utf-8 -*-
'''
Updated on August, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Unit test for configuration file generator
'''
import unittest

from lib.configuration import Configuration


class TestConfiguration(unittest.TestCase):

    def test_works(self):
        config = Configuration()
        config.next()
        config['random_seed'] = '234524'
        self.assertTrue(config['random_seed'] == '234524')
        content = config.generate_config()
        self.assertTrue('234524' in content)
        while(config.next()):
            content = config.generate_config()

    def test_invalid_template_file_name(self):
        with self.assertRaises(IOError):
            Configuration(template_file_name='/garabage/path/tom/nowhere/sadsf/template.cfg')

    def test_missing_parameter_name(self):
        config = Configuration()
        with self.assertRaises(Exception):
            config['alskdfjiejf;oaisdf'] = 'test'
        with self.assertRaises(Exception):
            config['alskdfjiejf;oaisdf'] == 'other'
