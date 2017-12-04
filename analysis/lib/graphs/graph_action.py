# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Class template for a graphed metric
'''


class GraphAction(object):
    '''
    Generic function every graphed metric has
    '''

    def create_graph(self):
        '''
        Create a graph from the metric data
        :param param: param_description
        :return: Object {'labels': label, 'data': data_list, 'series': series_list,
                         'type': type, }
        '''
        pass

    def _round(self, data_list):
        return map(lambda row: map(lambda x: round(x, 5), row), data_list)

    def _graph_structure(self, labels, data_list, series_list, chart_type,
                         title, stack_graph=False):
        return {'labels': labels, 'data': data_list, 'series': series_list, 'type': chart_type,
                'options': {
                    'title': {
                        'display': True,
                        'text': title
                    },
                    'responsive': True,
                    'elements': {'line': {'fill': False}},
                    'legend': {
                        'display': False
                    },
                    'scales': {
                        'yAxes': [
                            {
                                'stacked': stack_graph
                            }
                        ]
                    }
                }
               }
