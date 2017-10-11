# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

API for getting experiment metrics
'''

class CsvUtil(object):
    '''
    Utility for converting experiment data to a CVS format
    '''

    @staticmethod
    def convert(experiment_data_list):
        '''
        Return CSV formatted string
        '''
        # get the header values
        headers = {}
        for experiment in experiment_data_list:
            for grouping_name, grouping_vars in experiment.items():
                if grouping_name.startswith('_'):
                    continue
                for var_name, var_obj in grouping_vars.items():
                    headers[var_obj['short_name']] = {
                        'group': grouping_name, 'name': var_name}

        # generate CSV
        header_order = sorted(headers.keys())

        csv = ''
        csv += ','.join(header_order) + '\n'
        for data in experiment_data_list:
            row = []
            for header_name in header_order:
                header_obj = headers[header_name]
                row.append(str(data[header_obj['group']]
                           [header_obj['name']]['value']))
            csv += ','.join(row) + '\n'

        return csv
