# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Utility functions
'''


def average_degree(nx_graph):
    '''
    Calculate the average node degree
    :param nx_graph: networkx graph object
    :return: float average degree
    '''
    return sum(nx_graph.degree().values()) / float(nx_graph.number_of_nodes())
