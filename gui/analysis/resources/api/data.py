# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

API for getting experiment metrics
'''
import os
import json
import jmespath
from flask_restful import Resource
from flask import jsonify, current_app, request


class Data(Resource):
    '''
    Graph metrics
    '''

    def get(self, experiment_id):
        '''
        Only supports get operation
        '''
        if 'filter' not in request.args or not request.args.get('filter'):
            return jsonify({'items': []})

        experiment_config = current_app.config['EXPERIMENT_LIST'][experiment_id]

        routes_path = os.path.join(os.path.dirname(
            experiment_config['self']), 'processed.routing.json')
        expression = jmespath.compile(request.args.get('filter'))
        routes = []
        if os.path.exists(routes_path):
            count = 0
            with open(routes_path, 'r') as c_file:
                for line in c_file:
                    r_json = json.loads(line)
                    if expression.search(r_json):
                        routes.append(r_json)
                        count += 1
                        if count >= 1000:
                            break
        return jsonify({'items': routes})
