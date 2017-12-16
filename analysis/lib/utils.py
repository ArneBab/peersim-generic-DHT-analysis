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


def to_histogram_ints(values, start=None, stop=None, bin_funct=None):
    '''
    Convert a list of numbers into a histogram
    :param values: List of numbers
    :param start: The start value for the histogram
    :param stop: The stop value for the histogram
    :param bin_funct: When there are not natural bin sizes, they can be defined with this function
    :return: Labels list, data list, start value, stop value
    '''
    holder, start, stop = _to_histogram_(values, start, stop, bin_funct)
    histo = []
    labels = []
    for i in range(start, stop + 1):
        labels.append(i)
        if i in holder:
            histo.append(holder[i])
        else:
            histo.append(0)
    return labels, histo, start, stop

def to_histogram_floats(values, start=None, stop=None, bin_funct=None, labels_funct=None):
    '''
    Convert a list of numbers into a histogram
    :param values: List of numbers
    :param start: The start value for the histogram
    :param stop: The stop value for the histogram
    :param bin_funct: When there are not natural bin sizes, they can be defined with this function
    :param label_funct: Define the label values (same as the bin_funct)
    :return: Labels list, data list, start value, stop value
    '''
    holder, start, stop = _to_histogram_(values, start, stop, bin_funct)
    histo = []
    labels = []
    for i in labels_funct():
        labels.append(i)
        if i in holder:
            histo.append(holder[i])
        else:
            histo.append(0)
    return labels, histo, start, stop

def frange(start, stop, jump, places):
    '''
    Range for floats
    :param start: start
    :param stop: stop
    :param jump: step
    :param places: decimal places of percision
    :return: list of floats
    '''
    while start < stop:
        yield start
        start = round(start + jump, places)


def distance(x_l, y_l):
    '''
    Calculate the distance between x and y with a sircular address space
    :param x: first address
    :parame y: second address
    :return: difference
    '''
    return min([abs(x_l - y_l), abs((x_l + 1) - y_l), abs(x_l - (y_l + 1))])


def entropy_normalized(distro):
    '''
    Normalized Shannon Enropy
    :param distro: list of output probabilities
    :return: entropy
    '''
    entropy_value = entropy(distro)
    max_ent = max_entropy(distro)
    if max_ent == 0.0:
        return 0.0
    return entropy_value / float(max_entropy(distro))


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


def max_entropy(distro):
    '''
    Maximum Shannon entropy
    :param distro: List of the output distribution
    :return: Shannon maximum entropy
    '''
    return math.log(len(distro), 2)

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

def _to_histogram_(values, start=None, stop=None, bin_funct=None):
    if len(values) <= 0:
        return None, None, None

    def _natural(value): return value

    if bin_funct is None:
        bin_funct = _natural

    holder = {}
    largest = None
    smallest = None
    for value in values:
        bucket = bin_funct(value)
        # init entry
        if bucket not in holder:
            holder[bucket] = 0
        holder[bucket] = holder[bucket] + 1
        if largest is None:
            largest = bucket
        if smallest is None:
            smallest = bucket
        if bucket > largest:
            largest = bucket
        if bucket < smallest:
            smallest = bucket
    if start is None:
        start = smallest
    if stop is None:
        stop = largest
    return holder, start, stop

def timeit(method):
    ''' Logs a method call time '''
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        value = ''
        try:
            ts = time()
            value = method(*args, **kwargs)
            te = time()
            if len(args) > 0 and isinstance(args[0], dict) and 'id' in args[0]:
                logging.info(' -- %s -- %r ran in %2.2f sec', str(args[0]['id']), method.__name__, te-ts)
            else:
                logging.info('%r ran in %2.2f sec', method.__name__, te-ts)
        except Exception as ex:
            logging.error('ERROR')
            logging.error('ERROR')
            logging.error('ERROR')
            logging.error('    Error: %s ', str(ex))
            logging.error('ERROR')
            logging.error('ERROR')
            logging.error('ERROR')
        return value
    return wrapper
