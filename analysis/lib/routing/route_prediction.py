# -*- coding: utf-8 -*-
'''
Updated on SeptFeburary, 2018
@author: Todd Baumeister <tbaumeist@gmail.com>

Collection of route prediction functions
'''
from lib.utils import distance


def rank_greedy(node_id, target_location, nx_graph, cache=None):
    """Calculate the sorted routing choices for a node

    Arguments:
        node_id {int} -- ID of the node to calculate routing paths
        target_location {float} -- Target location to route to
        nx_graph {Graph} -- Netwrokx graph object
        cache {dict}  -- Dict used to store cached calculations

    Returns:
        List -- Ordered list of the routing preferences
    """
    if cache is not None and node_id in cache:
        return cache[node_id]
    peers = {}
    for child_id in nx_graph.neighbors(node_id):
        peers[child_id] = distance(
            nx_graph.node[child_id]['location'], target_location)

    ordered = sorted(peers.items(), key=lambda x: x[1])
    ordered_list = [i[0] for i in ordered]

    if cache is not None:
        cache[node_id] = ordered_list
    return ordered_list


def rank_greedy_2_hop(node_id, target_location, nx_graph, cache=None):
    """Calculate the sorted routing choices for a node when 2 hop look ahead is used

    Arguments:
        node_id {int} -- ID of the node to calculate routing paths
        target_location {float} -- Target location to route to
        nx_graph {Graph} -- Netwrokx graph object
        cache {dict}  -- Dict used to store cached calculations

    Returns:
        List -- Ordered list of the routing preferences
    """
    if cache is not None and node_id in cache:
        return cache[node_id]

    peers = {}
    for child_id in nx_graph.neighbors(node_id):
        peers[child_id] = distance(
            nx_graph.node[child_id]['location'], target_location)
        # peer of peers
        for child_child_id in nx_graph.neighbors(child_id):
            dist = distance(
                nx_graph.node[child_child_id]['location'], target_location)
            if dist < peers[child_id]:
                peers[child_id] = dist

    ordered = sorted(peers.items(), key=lambda x: x[1])
    ordered_list = [i[0] for i in ordered]

    if cache is not None:
        cache[node_id] = ordered_list
    return ordered_list
