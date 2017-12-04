# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files contents one line at a time
'''
import os
import json


class FileReader(object):
    '''
    Process a file one line at a time
    '''

    def __init__(self, json_actions):
        '''
        :param json_actions: JSONAction object list
        '''
        self.json_actions = json_actions

    def process(self, file_path):
        '''
        Process a given file by applying each file action to every line in the file
        :param file_path: Path to the file to read
        '''
        pass


class JSONFileReader(FileReader):
    '''
    Process a file one line at a time
    '''

    def process(self, file_path):
        '''
        Process a given file by applying each file action to every line in the file
        :param file_path: Path to the file to read
        '''
        # Does the file exist
        if not os.path.exists(file_path):
            raise Exception('Unable to find the file %s' % file_path)

        with open(file_path, 'r') as open_file:
            for line in open_file:
                json_object = json.loads(line)
                for action in self.json_actions:
                    action.process(json_object)
