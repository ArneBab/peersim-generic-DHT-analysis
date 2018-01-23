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


class SummaryGraphs(Resource):
    '''
    Graph metrics
    '''

    def get(self, variable):
        '''
        Only supports get operation
        '''
        experiment_config_file = os.path.join(
            current_app.config['DATA_DIRECTORY'], 'metrics.json')

        summary_data = {}
        if os.path.exists(experiment_config_file):
            with open(experiment_config_file, 'r') as c_file:
                summary_data = json.loads(c_file.read())
        variable_data = {}
        variable_data['graphs'] = summary_data['graphs'][variable]
        variable_data['data'] = summary_data['data'][variable]
        return jsonify(variable_data)
