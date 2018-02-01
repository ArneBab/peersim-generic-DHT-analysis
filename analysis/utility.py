# -*- coding: utf-8 -*-
'''
Updated on January, 2018
@author: Todd Baumeister <tbaumeist@gmail.com>

Main class for one off utility functions on the experiment data
'''
import os
import shutil
import json
from StringIO import StringIO
import pandas
from experiments import CONST_CONFIG, CONST_EXPERIMENT


def add_experiment_variable():
    '''
    Add a new experiment variable to existing experiment data
    '''
    base_directory = raw_input(
        '\tEnter directory path to experiments.json file: ')
    if not os.path.exists(base_directory):
        print '\tUnable to find the directory'
        return
    experiments_file_name = os.path.join(base_directory, 'experiments.json')
    if not os.path.exists(experiments_file_name):
        print '\tUnable to find the experiments.json file'
        return

    variable_name = raw_input('\tEnter new variable name: ')
    variable_value = raw_input('\tVariable value: ')

    # read the experiments file and patch it
    experiments_file_name_old = experiments_file_name + '.old'
    os.rename(experiments_file_name, experiments_file_name_old)
    with open(experiments_file_name_old, 'r') as experiments_file_old:
        with open(experiments_file_name, 'w') as experiments_file:
            experiments_data = json.loads(experiments_file_old.read())
            insertion_position = None

            # rename the paths in the experminats.json file
            for experiment in experiments_data:
                cfg_file_path = experiment[CONST_EXPERIMENT]
                json_file_path = experiment[CONST_CONFIG]

                # populate the list of existing variable
                existing_variables = os.path.dirname(
                    json_file_path).split(os.sep)
                new_variables = os.path.dirname(
                    json_file_path).split(os.sep)

                if insertion_position is None:
                    for i in range(0, len(existing_variables), 2):
                        print('\t[%d] %s' % (i, existing_variables[i]))
                    print('\t[%d] %s' % (len(existing_variables), 'END'))
                    insertion_position = int(
                        raw_input('\tSelect a position to insert the new variable: '))

                # add the new variable to the path
                _insert(variable_name, variable_value,
                        insertion_position, new_variables)

                # rename the paths
                experiment[CONST_EXPERIMENT] = os.path.join(os.path.join(
                    *new_variables), os.path.basename(cfg_file_path))
                experiment[CONST_CONFIG] = os.path.join(os.path.join(
                    *new_variables), os.path.basename(json_file_path))

                # move existing data
                new_folder = os.path.join(
                    *new_variables[0:insertion_position + 2])
                new_folder_full = os.path.join(
                    base_directory, new_folder) + os.sep
                if not os.path.exists(new_folder_full):
                    os.makedirs(new_folder_full)

                folder_prefix = os.path.join(
                    *new_variables[0:insertion_position])
                folder_prefix_full = os.path.join(
                    base_directory, folder_prefix)
                folder_prefix_full = os.path.abspath(folder_prefix_full)

                for entry in os.listdir(folder_prefix_full):
                    # make new folder
                    if entry == variable_name:
                        continue
                    shutil.move(os.path.join(
                        folder_prefix_full, entry), new_folder_full)

                # fix paths in the metrics.json
                metrics_file_path = os.path.dirname(experiment[CONST_CONFIG])
                metrics_file_path = os.path.abspath(os.path.join(
                    base_directory, metrics_file_path, 'metrics.json'))

                os.rename(metrics_file_path, metrics_file_path + '.old')
                with open(metrics_file_path + '.old', 'r') as existing_metrics_file:
                    with open(metrics_file_path, 'w') as new_metrics_file:

                        content = existing_metrics_file.read()
                        content = content.replace(folder_prefix, new_folder)
                        content = content.replace(
                            folder_prefix.replace('\\', '\\\\'),
                            new_folder.replace('\\', '\\\\'))

                        # add new variable
                        metric_obj = json.loads(content)
                        var_obj = {"full_name": variable_name,
                                   "short_name": variable_name,
                                   "description": "",
                                   "value": variable_value}
                        metric_obj['summations']['variables']['variables'].append(
                            var_obj)

                        # update variable list
                        data_frame = pandas.read_csv(StringIO(metric_obj['data']['variables']['variables']))
                        data_frame[variable_name] = variable_value
                        metric_obj['data']['variables']['variables'] = data_frame.to_csv(index=False)

                        new_metrics_file.write(json.dumps(metric_obj))

            experiments_file.write(json.dumps(experiments_data))


def finished():
    '''
    Quit the program
    '''
    exit(0)


def _insert(variable, value, position, path_list):
    path_list.insert(position, variable)
    path_list.insert(position + 1, value)


if __name__ == '__main__':
    options = [add_experiment_variable, finished]

    while True:
        print '\n\nActions:'
        count = 0
        for opt in options:
            print '[%d] %s' % (count, opt.func_name.replace('_', ' '))
            count += 1

        action_selected = raw_input("Select a #: ")
        print ''
        options[int(action_selected)]()
