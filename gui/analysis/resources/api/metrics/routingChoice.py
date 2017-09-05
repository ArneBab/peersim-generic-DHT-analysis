# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

API for getting experiment information
'''
import os
import json
from flask_restful import Resource
from flask import jsonify, current_app


class RoutingChoice(Resource):
    '''
    Represents a list of experiments
    '''

    def get(self, id):
        '''
        Only supports get operation
        '''
        experiment_config = current_app.config['EXPERIMENT_LIST'][id]

        choice_metrics_path = os.path.join(os.path.dirname(
            experiment_config['self']), 'metrics', 'stats.json')
        metrics = {}
        if os.path.exists(choice_metrics_path):
            with open(choice_metrics_path, 'r') as c_file:
                metrics = json.loads(c_file.read())
        return jsonify(metrics)
