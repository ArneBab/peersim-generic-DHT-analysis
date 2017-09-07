# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Utility functions
'''
import os
import networkx as nx

def get_nx_graph():
    '''
    Get the test network graph
    '''
    current_dir = os.path.dirname(__file__)
    graph_file = os.path.join(current_dir, 'resources', 'size_14.gml')
    nx_graph = nx.read_gml(graph_file, 'id')
    return nx_graph

def get_route_json_path():
    '''
    Get the test routing data file path
    '''
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, 'resources', 'route.json')

def list_equals(list_1, list_2):
    '''
    Check if the two lists are equal
    '''
    if len(list_1) != len(list_2):
        return False

    for i in list_1:
        if i not in list_2:
            return False
    return True