# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Find file bases on pattern and process them
'''
import os
import glob

class FileFinder(object):
    '''
    Find files in a directory and process them
    '''

    def __init__(self, file_reader_list):
        '''
        :param file_reader_list: List of FileReader objects
        '''
        self.file_reader_list = file_reader_list

    def process(self, base_directory, file_pattern):
        '''
        Find file in the given base directory that contain the file pattern
        :param base_directory: Directory to start recursive search from
        :param file_pattern: File name pattern to look for
        '''
        if not os.path.exists(base_directory):
            raise Exception('The directory %s does not exists' % base_directory)

        search_pattern = os.path.abspath(base_directory) + file_pattern
        found_files = sorted(glob.glob(search_pattern))

        for file_path in found_files:
            for reader in self.file_reader_list:
                reader.process(file_path)
