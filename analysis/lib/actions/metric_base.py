# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files
'''
import math
from StringIO import StringIO
import pandas
import numpy


class MetricBase(object):
    '''
    Generic interface for JSON based actions
    '''

    def __init__(self):
        self.data_frame = pandas.DataFrame()
        self._columns_to_add = []
        self._rows_to_add = []
        self._version = 1.0

    def process(self, data_object):
        '''
        Process a given file
        :param data_object: Data object
        :return: Updated data_object reference
        '''
        if data_object is None:
            raise Exception('Data object is null')
        return data_object

    def on_start(self, file_path):
        '''
        Start of processing a new file
        :param file_path: Full path to the file being processed
        '''
        pass

    def on_stop(self):
        '''
        End of processing a new file
        '''
        # create a data frame from the cached columns and rows
        # first normalize the rows to match the column length
        columns = list(self.data_frame.columns) + self._columns_to_add
        column_len = len(columns)
        for row_index in range(len(self._rows_to_add)):
            row = self._rows_to_add[row_index]
            self._rows_to_add[row_index] = row + \
                [numpy.nan] * (column_len - len(row))
        # get existing data
        existing_data = [list(row.values)
                         for _, row in self.data_frame.iterrows()]
        # normalize existing data
        for row_index in range(len(existing_data)):
            row = existing_data[row_index]
            existing_data[row_index] = row + \
                [numpy.nan] * (column_len - len(row))
        # create Data frame
        self.data_frame = pandas.DataFrame(
            existing_data + self._rows_to_add, columns=columns)
        # clear cached data to add
        self._columns_to_add = []
        self._rows_to_add = []

    def add_column(self, column_name):
        '''
        Add a new column to the data set if it doesn't already exist
        :param column_name: Name of the column
        '''
        column_name = column_name.strip()
        if column_name in self._columns_to_add or column_name in self.data_frame.columns:
            return
        self._columns_to_add.append(column_name)

    def add_row(self, row_values):
        '''
        Add a new row to the end of the data set
        :param row_values: List of the new row values. Throws an exception if the
        lenght of the row is longer than the columns. Will pad the row with
        empty values if it doesn't have a value for each column.
        '''
        row_len = len(row_values)
        column_len = len(self._columns_to_add) + len(self.data_frame.columns)
        # row can't be longer than columns
        if row_len > column_len:
            raise Exception('Unable to add a row longer than defined columns')
        # add the new row to the end of the data set
        self._rows_to_add.append(row_values)

    def merge(self, other):
        '''
        Merge the data frame of this object with the data frame of another
        :param other: JSONAction
        '''
        # check that the columns match
        for column_name in other.data_frame.columns:
            self.add_column(column_name)
        # insert data from other into self
        for _, row in other.data_frame.iterrows():
            self.add_row(list(row.values))
        # call on stop to merge data into the data frame
        self.on_stop()

    def force_summation(self):
        '''
        Determine if summation must always be run
        :return: True if summation need to be recalculated evey time
        '''
        return False

    def to_csv(self, index=False):
        '''
        Get the JSON representation of this object
        :return: JSON string
        '''
        if len(self.data_frame.columns) <= 0 and len(self.data_frame) <= 0:
            return ''
        return self.data_frame.to_csv(index=index)

    def to_string(self, index=False):
        """Convert to string object
        
        Keyword Arguments:
            index {bool} -- Include the pandas index (default: {False})

        Returns:
            dict -- Returns dict string object representing this metric
        """
        return {'version': self.get_version(), 'csv_string': self.to_csv(index)}

    def get_version(self):
        """Get the version of the metric

        Returns:
            float -- Version number
        """
        return self._version

    def load(self, obj_string):
        """Load a metric from stored data

        Arguments:
            obj_string {dict} -- CVS String representing object returned from to_string

        Returns:
            bool -- Returns true if the data was successfully loaded
        """
        # check if just string was passed in (pre-version data)
        # set default version of 1.0
        if not isinstance(obj_string, dict):
            obj_string = {'version': 1.0, 'csv_string': obj_string}

        # load the string data
        if obj_string['version'] != self._version:
            return False
        if not obj_string['csv_string']:
            return True
        self.data_frame = pandas.read_csv(StringIO(obj_string['csv_string']))
        return True

    def _w(self, value, description, short_name, full_name):
        return {'value': value, 'description': description,
                'short_name': short_name, 'full_name': full_name}

    def _round(self, data_list):
        return map(lambda row: map(lambda x: round(x, 5), row), data_list)

    def _replace_nan(self, metrics_list):
        for metric in metrics_list:
            if math.isnan(metric['value']):
                metric['value'] = 0.0

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
                    },
                    'tooltips': {
                        'mode': 'single'
                    }
                }}
