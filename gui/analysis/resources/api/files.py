# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

API for traversing experiments
'''
import os
from flask_restful import Resource
from flask import request, jsonify, current_app
from marshmallow import Schema, fields


class FilePathSchema(Schema):
    '''
    Class for parsing json input/output
    '''
    name = fields.Str()
    url = fields.Str()

    class Meta:
        strict = True


FILES_SCHEMA = FilePathSchema(many=True)


class FileList(Resource):
    '''
    Represents a list of file paths to/from experiments
    '''

    def get(self):
        '''
        Only supports get operation
        '''
        current_path = ''
        if 'path' in request.args:
            current_path = request.args['path']

        data_dir = os.path.abspath(current_app.config['DATA_DIRECTORY'])
        full_path = os.path.abspath(os.path.join(data_dir, current_path))
        if not full_path.startswith(data_dir):
            full_path = data_dir

        # get bread crumbs
        path_diff = full_path.replace(data_dir, '')
        bread_crumbs = []
        working_path = '#/files'
        for path in path_diff.split('/'):
            if path == '':
                continue
            working_path = working_path + '/' + path
            bread_crumbs.append({'name': path, 'url': working_path})

        # add home
        if len(bread_crumbs) > 0:
            bread_crumbs.insert(0, {'name': 'home', 'url': '#/'})

        all_files = [file_name for file_name in os.listdir(full_path)]
        # check if at the end of the path
        if 'config.json' in all_files:
            return jsonify({'nextFilePaths': [],
                            'breadCrumbs': FILES_SCHEMA.dump(bread_crumbs).data})

        # get the next files
        files = []
        for file_name in all_files:
            files.append({'name': file_name, 'url': '#/files' +
                                                    path_diff + '/' + file_name})

        return jsonify({'nextFilePaths': FILES_SCHEMA.dump(files).data,
                        'breadCrumbs': FILES_SCHEMA.dump(bread_crumbs).data})
