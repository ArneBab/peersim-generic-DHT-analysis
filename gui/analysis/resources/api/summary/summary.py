# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

API for getting experiment metrics
'''
import os
import json
from flask_restful import Resource
from flask import jsonify, current_app


class Summary(Resource):
    '''
    Graph metrics
    '''

    def get(self):
        '''
        Only supports get operation
        '''
        experiment_config_file = os.path.join(
            current_app.config['DATA_DIRECTORY'], 'summary.json')

        summary = []
        if os.path.exists(experiment_config_file):
            with open(experiment_config_file, 'r') as c_file:
                summary = json.loads(c_file.read())

        # get the header values
        headers = {}
        for experiment in summary:
            for grouping_name, grouping_vars in experiment.items():
                if grouping_name.startswith('_'):
                    continue
                for var_name, var_obj in grouping_vars.items():
                    headers[var_obj['short_name']] = {'group': grouping_name, 'name': var_name}

        # get the experiment variables
        variables = []
        for experiment in summary:
            for grouping_name, grouping_vars in experiment.items():
                if grouping_name == 'variables':
                    variables = sorted(grouping_vars.keys())
                    break

        return jsonify({'headers': headers, 'variables': variables, 'data' : summary})


class SummaryGraphs(Resource):
    '''
    Graph metrics
    '''

    def get(self, variable):
        '''
        Only supports get operation
        '''
        experiment_config_file = os.path.join(
            current_app.config['DATA_DIRECTORY'], 'summary_display.json')

        summary_data = {}
        if os.path.exists(experiment_config_file):
            with open(experiment_config_file, 'r') as c_file:
                summary_data = json.loads(c_file.read())
        variable_data = summary_data['graphs'][variable]
        return jsonify(variable_data)
