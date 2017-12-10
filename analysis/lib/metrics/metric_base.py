# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files
'''
from StringIO import StringIO
import pandas
import numpy


class MetricBase(object):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self):
        self.data_frame = pandas.DataFrame()

    def process(self, json_object):
        '''
        Process a given file
        :param json_object: JSON object
        '''
        if json_object is None:
            raise Exception('JSON object is null')

    def add_column(self, column_name):
        '''
        Add a new column to the data set if it doesn't already exist
        :param column_name: Name of the column
        '''
        column_name = column_name.strip()
        if column_name in self.data_frame:
            return
        # add an empty column
        self.data_frame[column_name] = numpy.nan

    def add_row(self, row_values):
        '''
        Add a new row to the end of the data set
        :param row_values: List of the new row values. Throws an exception if the
        lenght of the row is longer than the columns. Will pad the row with
        empty values if it doesn't have a value for each column.
        '''
        row_len = len(row_values)
        column_len = len(self.data_frame.columns)
        # row can't be longer than columns
        if row_len > column_len:
            raise Exception('Unable to add a row longer than defined columns')
        # add empty values for missing row columns
        row_values = row_values + [numpy.nan] * (column_len - row_len)
        # add the new row to the end of the data set
        self.data_frame.loc[len(self.data_frame)] = row_values

    def merge(self, other):
        '''
        Merge the data frame of this object with the data frame of another
        :param other: JSONAction
        '''
        # check that the columns match
        for column_name in other.data_frame.columns:
            self.add_column(column_name)
        # insert data from other into self
        for i_index in range(len(other.data_frame)):
            row = []
            i_row = other.data_frame.iloc[i_index]
            # make sure column values match up
            for column_name in self.data_frame.columns:
                if column_name not in i_row:
                    row.append(numpy.nan)
                else:
                    row.append(i_row[column_name])
            self.add_row(row)

    def to_csv(self):
        '''
        Get the JSON representation of this object
        :return: JSON string
        '''
        return self.data_frame.to_csv(index=False)

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

    @classmethod
    def load(cls, csv_string):
        '''
        Load a JSON action from a CSV string
        :param csv_string: String representation of a JSONAction object
        :return: object
        '''
        action = cls()
        action.data_frame = pandas.read_csv(StringIO(csv_string))
        return action
