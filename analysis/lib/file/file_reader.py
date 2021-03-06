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

    def __init__(self, metric_actions):
        '''
        :param json_actions: JSONAction object list
        '''
        self.metric_actions = metric_actions

    def process(self, file_path):
        '''
        Process a given file by applying each file action to every line in the file
        :param file_path: Path to the file to read
        '''
        pass

    def on_start(self, file_path):
        '''
        Start of processing a new file
        :param file_path: Full path to the file being processed
        '''
        pass

    def on_stop(self):
        '''
        End of processing a new file
        '''
        pass

    def _send_data(self, data):
        for action in self.metric_actions:
            data = action.process(data)


class ClassReader(FileReader):
    '''
    Process a file one line at a time
    '''

    def __init__(self, metric_actions, class_type):
        '''
        :param json_actions: JSONAction object list
        :param class_type: Class to be constructed. Constructor will be passed
        '''
        super(ClassReader, self).__init__(metric_actions)
        self.class_type = class_type

    def process(self, file_path):
        '''
        Process a given file by applying each file action to every line in the file
        :param file_path: Path to the file to read
        '''
        if not os.path.exists(file_path):
            raise Exception('Unable to find the directory %s' % file_path)

        # call on start
        for action in self.metric_actions:
            action.on_start(file_path)
        # process file
        self._send_data(self.class_type(file_path))
        # call on stop
        for action in self.metric_actions:
            action.on_stop()


class TextFileReader(FileReader):
    '''
    Process a file one line at a time as text
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
            # call on start
            for action in self.metric_actions:
                action.on_start(file_path)
            # process each line
            for line in open_file:
                self._send_data(line)
            # call on stop
            for action in self.metric_actions:
                action.on_stop()


class JSONFileReader(TextFileReader):
    ''' Read each line as a JSON object '''

    def _send_data(self, data):
        super(JSONFileReader, self)._send_data(json.loads(data))
