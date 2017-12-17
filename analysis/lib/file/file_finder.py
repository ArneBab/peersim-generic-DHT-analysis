# -*- coding: utf-8 -*-
'''
Updated on Nov, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Find file bases on pattern and process them
'''
import os
import fnmatch
import zipfile


class FileFinder(object):
    '''
    Find files in a directory and process them
    '''

    def __init__(self, file_reader_list):
        '''
        :param file_reader_list: List of FileReader objects
        '''
        self.file_reader_list = file_reader_list

    def process(self, base_directory, file_pattern, skip_base_directory=False):
        '''
        Find file in the given base directory that contain the file pattern
        :param base_directory: Directory to start recursive search from
        :param file_pattern: File name pattern to look for
        :param skip_base_directory: Skip looking for file in the base directory
        '''
        if not os.path.exists(base_directory):
            raise Exception('The directory %s does not exists' %
                            base_directory)

        found_files = []
        for root, dirnames, filenames in os.walk(base_directory):
            if skip_base_directory and root == base_directory:
                continue
            for filename in self._match(filenames, file_pattern):
                found_files.append(os.path.abspath(
                    os.path.join(root, filename)))

        for reader in self.file_reader_list:
            reader.on_start(base_directory)
        for file_path in found_files:
            self._process_file(file_path)
        for reader in self.file_reader_list:
            reader.on_stop()

        self.on_stop()

    def on_stop(self):
        '''
        End of processing files
        '''
        pass

    def _match(self, file_names, file_pattern):
        return fnmatch.filter(sorted(file_names), file_pattern)

    def _process_file(self, file_path):
        for reader in self.file_reader_list:
            reader.process(file_path)


class FileArchiver(FileFinder):
    ''' Archive files in a zip '''

    def __init__(self, output_directory):
        super(FileArchiver, self).__init__([])
        self.output_directory_path = output_directory
        self.output_file_name = os.path.join(output_directory, 'archive.zip')
        self.output_file = None
        # is there already an archive
        if not os.path.exists(self.output_file_name):
            self.output_file = zipfile.ZipFile(
                self.output_file_name, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)

    def on_stop(self):
        if self.output_file is not None:
            self.output_file.close()
        self.output_file = None

    def exists(self):
        return os.path.exists(self.output_file_name)

    def _match(self, file_names, file_pattern):
        included = set(file_names)
        excluded = set()
        for pattern in file_pattern:
            for file_found in fnmatch.filter(sorted(file_names), pattern):
                excluded.add(file_found)
        excluded.add('archive.zip')
        return included - excluded

    def _process_file(self, file_path):
        if self.output_file is not None:
            rel_file_path = file_path.replace(
                self.output_directory_path + os.sep, '')
            self.output_file.write(file_path, rel_file_path)


class FileCleaner(FileArchiver):
    ''' delete found files '''

    def _process_file(self, file_path):
        os.remove(file_path)
