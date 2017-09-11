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

def to_histogram_numbers(values, start=None, stop=None):
    '''
    Convert a list of numbers into a histogram
    :param values: List of numbers
    :param start: The start value for the histogram
    :param stop: The stop value for the histogram
    :return: histogram list, start value, stop value
    '''
    if len(values) <= 0:
        return [], None, None
    holder = {}
    largest = None
    smallest = None
    for value in values:
        # init entry
        if value not in holder:
            holder[value] = 0
        holder[value] = holder[value] + 1
        if largest is None:
            largest = value
        if smallest is None:
            smallest = value
        if value > largest:
            largest = value
        if value < smallest:
            smallest = value
    if start is None:
        start = smallest
    if stop is None:
        stop = largest
    histo = [0 for i in range(start, stop+1)]
    for i in range(start, stop+1):
        if i in holder:
            histo[i-start] = holder[i]
    return histo, start, stop

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
    for p in distro:
        entropy = entropy + (p * math.log(p, 2))
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
