# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

API for getting experiment metrics
'''
import os
import json
from flask_restful import Resource
from flask import current_app, Response
from analysis.lib.csv import CsvUtil


class Csv(Resource):
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
        csv = CsvUtil.convert(summary)

        return Response(csv, mimetype="text/csv",
                        headers={"Content-disposition":
                                 "attachment; filename=summary.csv"})
