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
