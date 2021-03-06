# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

API for getting experiment metrics
'''
import os
import json
import zipfile
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
        if 'filter' not in request.args:
            return jsonify({'items': []})

        experiment_config = current_app.config['EXPERIMENT_LIST'][experiment_id]

        archive_path = os.path.abspath(os.path.join(os.path.dirname(
            experiment_config['self']), 'archive.zip'))
        normal_path = os.path.abspath(os.path.join(os.path.dirname(
            experiment_config['self']), 'sender_set.routing.json'))

        expression = None
        if request.args.get('filter'):
            expression = jmespath.compile(request.args.get('filter'))
        routes = []

        if os.path.exists(normal_path):
            # read from normal file
            with open(normal_path, 'r') as c_file:
                self._filter(c_file, expression, routes)
        elif os.path.exists(archive_path):
            # read from zip file
            with zipfile.ZipFile(archive_path, allowZip64=True) as z_file:
                if 'sender_set.routing.json' in z_file.namelist():
                    with z_file.open('sender_set.routing.json') as c_file:
                        self._filter(c_file, expression, routes)

        return jsonify({'items': routes})

    def _filter(self, c_file, expression, routes):
        count = 0
        for line in c_file:
            r_json = json.loads(line)
            if expression is None or expression.search(r_json):
                routes.append(r_json)
                count += 1
                if count >= 100:
                    break
        
