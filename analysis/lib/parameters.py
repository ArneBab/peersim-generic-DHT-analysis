# -*- coding: utf-8 -*-
'''
Updated on Feburary, 2018
@author: Todd Baumeister <tbaumeist@gmail.com>

Stores the peersim variable values to enumerate over
'''


class Parameters(object):
    """Stores the peersim variable values to enumerate over
    """

    # repeat must be last
    _variables = [('topology_type', ['random_erdos_renyi',
                                     'small_world', 'structured']),
                  ('router_type', ['DHTRouterGreedy']),
                  ('router_randomness', [0.0, 0.05, 0.1]),
                  ('router_can_backtrack', ['true']),
                  ('router_drop_rate', [0.0]),
                  ('look_ahead', [1, 2]),
                  ('adversary_count', ['1%']),
                  ('router_loop_detection', ['GUIDLoopDetection', 
                                             'NoLoopDetection']),
                  ('size', [1000, 2000, 3000, 4000]),
                  ('degree', [10, 12, 14, 16]),
                  ('repeat', [1, 2, 3]),
                  ]

    @staticmethod
    def get_parameters():
        """Get the parameter options
        
        Returns:
            dict -- Dictionary of the parameters and options
        """

        params = {}
        for name, options in Parameters._variables:
            params[name] = options
        return params

    @staticmethod
    def get_parameter_names():
        '''
        Get the used experiment parameters
        :return: Ordered list of parameter names
        '''
        return [name for name, _ in Parameters._variables]
