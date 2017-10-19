# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

API for getting experiment information
'''
import os
import json

from flask_restful import Resource
from flask import jsonify, current_app, send_from_directory


class ExperimentList(Resource):
    '''
    Represents a list of experiments
    '''

    def get(self):
        '''
        Only supports get operation
        '''
        experiment_config = current_app.config['EXPERIMENT_LIST'][0]
        metrics_path = os.path.join(os.path.dirname(
            experiment_config['self']), 'metrics', 'consolidated.json')
        with open(metrics_path, 'r') as m_file:
            experiment_metrics = json.loads(m_file.read())

        variables = sorted(experiment_metrics['variables'].keys())

        var_list = []
        for var in variables:
            var_list.append({'label': str(var), 'children':[], 'data':'/#/variables/' + str(var)})

        return jsonify({'experiments': current_app.config['EXPERIMENT_HIERARCHY'], 'variables': var_list})


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

class ExperimentCSV(Resource):
    '''
    Represents a list of experiments
    '''

    def get(self, experiment_id, csv_file):
        '''
        Only supports get operation
        '''
        experiment_config = current_app.config['EXPERIMENT_LIST'][experiment_id]

        csv_path = os.path.join(os.path.dirname(
            experiment_config['self']), 'metrics', os.path.basename(csv_file))
        header = None
        csv = []
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as c_file:
                for line in c_file:
                    parsed = line.split(',')
                    if header is None:
                        header = parsed
                        continue
                    csv.append(parsed)
        return jsonify({'headers': header, 'data': csv})

class ExperimentStatic(Resource):
    '''
    Represents a list of experiments
    '''

    def get(self, experiment_id, static_file):
        '''
        Only supports get operation
        '''
        experiment_config = current_app.config['EXPERIMENT_LIST'][experiment_id]
        static_path = os.path.join(os.path.dirname( experiment_config['self']), 'metrics')
        return send_from_directory(static_path, os.path.basename(static_file))