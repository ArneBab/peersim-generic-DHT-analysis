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


class ExperimentList(Resource):
    '''
    Represents a list of experiments
    '''

    def get(self):
        '''
        Only supports get operation
        '''
        return jsonify({'items': current_app.config['EXPERIMENT_LIST']})


class Experiment(Resource):
    '''
    Represents a list of experiments
    '''

    def get(self, experiment_id):
        '''
        Only supports get operation
        '''
        experiment_config = current_app.config['EXPERIMENT_LIST'][experiment_id]

        metrics_path = os.path.join(os.path.dirname(
            experiment_config['self']), 'metrics', 'consolidated.json')
        with open(metrics_path, 'r') as m_file:
            experiment_config['metrics'] = json.loads(m_file.read())
        return jsonify(experiment_config)
