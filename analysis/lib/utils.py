# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Utility functions
'''
import math
import logging
import functools
from time import time


def average_degree(nx_graph):
    '''
    Calculate the average node degree
    :param nx_graph: networkx graph object
    :return: float average degree
    '''
    return sum(dict(nx_graph.degree()).values()) / float(nx_graph.number_of_nodes())


def distance(x_l, y_l):
    '''
    Calculate the distance between x and y with a sircular address space
    :param x: first address
    :parame y: second address
    :return: difference
    '''
    value = min([abs(x_l - y_l), abs((x_l + 1) - y_l), abs(x_l - (y_l + 1))])
    return round(value, 10)


def entropy_normalized(distro, total_node_count):
    """Normalized Shannon Entropy
    
    Arguments:
        distro {list} -- List of probabilities
        total_node_count {int} -- Total number of nodes in the topology
    
    Returns:
        float -- Entropy
    """
    entropy_value = entropy(distro)
    max_ent = max_entropy(total_node_count)
    if max_ent == 0.0:
        return 0.0
    return entropy_value / float(max_ent)


def entropy(distro):
    '''
    Shannon Enropy
    :param distro: list of output probabilities
    :return: entropy
    '''
    entropy_value = 0
    for prob in distro:
        # log of 0.0 is not defined
        if prob <= 0.0:
            continue
        entropy_value += (prob * math.log(prob, 2))
    entropy_value = entropy_value * -1
    return entropy_value


def max_entropy(total_node_count):
    """Maximum Shannon entropy
    
    Arguments:
        total_node_count {int} -- Total nodes in topology
    
    Returns:
        float -- Maximum entropy
    """
    return math.log(total_node_count, 2)


def percent(selected, total):
    '''
    Calculate the percentage
    :param selected: Items selected
    :param total: Total items
    :return: value between 1.0 and 0.0
    '''
    if total == 0:
        return 0.0
    return selected / float(total)


def timeit(method):
    ''' Logs a method call time '''
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        ''' Function wrapper '''
        value = ''
        try:
            t_s = time()
            value = method(*args, **kwargs)
            t_e = time()
            if len(args) > 0 and isinstance(args[0], dict) and 'id' in args[0]:
                logging.info(' -- %s -- %r ran in %2.2f sec',
                             str(args[0]['id']), method.__name__, t_e - t_s)
            else:
                logging.info('%r ran in %2.2f sec', method.__name__, t_e - t_s)
        except Exception as ex:
            logging.error('ERROR')
            logging.error('ERROR')
            logging.error('ERROR')
            if len(args) > 0 and isinstance(args[0], dict) and 'id' in args[0]:
                logging.exception('     -- %s -- Error: %s ',
                                  str(args[0]['id']), str(ex))
            else:
                logging.exception('    Error: %s ', str(ex))
            logging.error('ERROR')
            logging.error('ERROR')
            logging.error('ERROR')
        return value
    return wrapper


def metric_iter(metric_dic):
    '''
    Iterate over a Metric storage object
    :param metric_dic: Store object
    :return: yields (group name, metric name, metric object)
    '''
    for group_name, group_obj in metric_dic.items():
        for metric_name, metric_obj in group_obj.items():
            yield (group_name, metric_name, metric_obj)


def metric_add(metric_obj, metric_dict, *args):
    '''
    Add item to a Metric storage
    :param metric_obj: The metric object
    :param metric_dict: The metric store to append the metric_obj to
    :param args: The path to store the metric_obj at
    :return: reference to the metric store
    '''
    if len(args) <= 0:
        raise Exception('Must specify a storage path')
    if len(args) == 1:
        if args[0].startswith('___'):
            return
        metric_dict[args[0]] = metric_obj
        return
    next_path = args[1:]
    if args[0] not in metric_dict:
        metric_dict[args[0]] = {}
    metric_add(metric_obj, metric_dict[args[0]], *next_path)
    return metric_dict


def metric_get(group_name, metric_name, metric_dict):
    '''
    Get item from a Metric storage
    :param group_name: Name of the group
    :param metric_name: Name of the metric
    :param metric_dict: The metric store to append the metric_obj to
    :return: reference to the metric object or None if not found
    '''
    if group_name in metric_dict and metric_name in metric_dict[group_name]:
        return metric_dict[group_name][metric_name]
    return None


def metric_merge(metric_one, metric_two):
    '''
    Merge two metric stores together
    :param metric_one: First metric storage. metric_two is merged into this structure.
    :param metric_two: Second metric storage
    :return: reference to the metric store with the added entries
    '''
    if metric_one is None:
        return metric_two
    for g_name, m_name, m_obj in metric_iter(metric_two):
        metric_add(m_obj, metric_one, g_name, m_name)
    return metric_one
