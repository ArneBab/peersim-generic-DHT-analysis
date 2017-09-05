# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

API for getting experiment information
'''
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

    def get(self, id):
        '''
        Only supports get operation
        '''
        experiment_config = current_app.config['EXPERIMENT_LIST'][id]
        return jsonify(experiment_config)
