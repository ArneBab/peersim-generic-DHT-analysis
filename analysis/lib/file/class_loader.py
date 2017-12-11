# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Framework for processing a files contents one line at a time
'''
import os
from lib.file.file_reader import FileReader


class ClassLoader(FileReader):
    '''
    Process a file one line at a time
    '''
    def __init__(self, class_type):
        '''
        :param class_type: Class to be constructed. Constructor will be passed
        a single parameter with the file path
        '''
        self.class_type = class_type
        self.class_instance = []

    def process(self, file_path):
        '''
        Process a given file by applying each file action to every line in the file
        :param file_path: Path to the file to read
        '''
        # Does the file exist
        if not os.path.exists(file_path):
            raise Exception('Unable to find the directory %s' % file_path)

        self.class_instance.append(self.class_type(file_path))
