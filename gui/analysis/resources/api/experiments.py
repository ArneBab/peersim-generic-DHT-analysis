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
        experiment_config = current_app.config['EXPERIMENT_LIST'][0]
        metrics_path = experiment_config['self']
        with open(metrics_path, 'r') as m_file:
            experiment_metrics = json.loads(m_file.read())

        exp_vars = experiment_metrics['summations']['variables']['variables']
        variables = sorted([var['full_name'] for var in exp_vars])

        var_list = []
        for var in variables:
            var_list.append({'label': str(var), 'children': [],
                             'data': '/#/variables/' + str(var)})

        return jsonify({'experiments': current_app.config['EXPERIMENT_HIERARCHY'],
                        'variables': var_list})


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
            experiment_config['self']), 'metrics.json')
        with open(metrics_path, 'r') as m_file:
            exp = json.loads(m_file.read())
        exp['id'] = experiment_config['id']
        return exp
