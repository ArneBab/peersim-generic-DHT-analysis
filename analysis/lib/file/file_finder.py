# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Find file bases on pattern and process them
'''
import os
import fnmatch

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

        found_files = []
        for root, dirnames, filenames in os.walk(base_directory):
            for filename in fnmatch.filter(sorted(filenames), file_pattern):
                found_files.append(os.path.abspath(os.path.join(root, filename)))

        for file_path in found_files:
            for reader in self.file_reader_list:
                reader.process(file_path)
