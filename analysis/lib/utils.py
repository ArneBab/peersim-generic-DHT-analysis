# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Utility functions
'''
import math


def average_degree(nx_graph):
    '''
    Calculate the average node degree
    :param nx_graph: networkx graph object
    :return: float average degree
    '''
    return sum(nx_graph.degree().values()) / float(nx_graph.number_of_nodes())


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

def to_histogram_floats(values, step, places, start=None, stop=None, bin_funct=None):
    '''
    Convert a list of numbers into a histogram
    :param values: List of numbers
    :param step: step size to use
    :param places: decimal places of percision
    :param start: The start value for the histogram
    :param stop: The stop value for the histogram
    :param bin_funct: When there are not natural bin sizes, they can be defined with this function
    :return: Labels list, data list, start value, stop value
    '''
    holder, start, stop = _to_histogram_(values, start, stop, bin_funct)
    histo = []
    labels = []
    for i in frange(start, stop + step, step, places):
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
    entropy = 0
    for prob in distro:
        entropy = entropy + (prob * math.log(prob, 2))
    entropy = entropy * -1
    max_ent = max_entropy(distro)
    if max_ent == 0.0:
        return 0.0
    return entropy / float(max_entropy(distro))


def max_entropy(distro):
    '''
    Maximum Shannon entropy
    :param distro: List of the output distribution
    :return: Shannon maximum entropy
    '''
    return math.log(len(distro), 2)

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
