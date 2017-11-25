# -*- coding: utf-8 -*-
'''
Updated on October, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Run the final experiment comparisions
'''
import json
import pandas
import numpy
from scipy import stats
from lib.configuration import Configuration

def _compare(first, second):
    try:
        f_first = float(first)
        f_second = float(second)

        first = f_first
        second = f_second
    except Exception:
        pass
    if first < second:
        return -1
    if first > second:
        return 1
    return 0

class SummaryMetrics(object):
    '''
    Calculate summary metrics of all the experiments
    '''

    def calculate(self, list_experiment_groups_metrics):
        exp_groups = []
        # load the experiment data
        for exp_group_file in list_experiment_groups_metrics:
            with open(exp_group_file, 'r') as e_file:
                exp_groups.append(json.loads(e_file.read()))
        return exp_groups

    def process(self, experiments_data_list):
        '''
        Generate the display data for the visualization site
        :param experiments_data_list: List of experiment data. Output of calculate method
        :return: experiment data object
        '''
        # get the variables group names
        group_names = []
        for exp in experiments_data_list:
            for group_name, group_list in exp.items():
                if group_name == 'variables':
                    group_names = group_list.keys()
                    break

        # group data by variable hash
        # variable -> {group} -> {metric} -> {config hash} -> {variable value} -> metric value obj
        new_data = {}
        for var_group in sorted(group_names):
            new_data[var_group] = {}
            exp_datas = new_data[var_group]

            for exp in experiments_data_list:
                # get variable list
                variables = exp['variables']
                var_hash = Configuration.get_hash_name(variables, [var_group, 'repeat'])
                var_hash = var_hash.lower().replace('dhtrouter', '').replace('random', 'rand')
                var_value = variables[var_group]['value']

                for group_name, group_obj in exp.items():
                    # Don't process raw data or varaibles
                    if group_name in ['variables', '_raw']:
                        continue

                    if group_name not in exp_datas:
                        exp_datas[group_name] = {}

                    for metric_name, metric_obj in group_obj.items():
                        if metric_name not in exp_datas[group_name]:
                            exp_datas[group_name][metric_name] = {}

                        metric_data = exp_datas[group_name][metric_name]
                        if var_hash not in metric_data:
                            metric_data[var_hash] = {}
                        metric_data[var_hash][var_value] = metric_obj

        # generate graphs
        correlations = {}
        graphs = {}
        for variable, exp_datas in new_data.items():
            for group_name, group_objs in exp_datas.items():
                corr_headers = []
                corr_data = {}
                for metric_name in sorted(group_objs.keys()):
                    metric_objs = group_objs[metric_name]
                    series_list = []
                    data = []
                    labels = []
                    corr_headers.append(metric_name)
                    overall_corr_data = {variable:[], metric_name:[]}
                    for hash_grouping, var_values in metric_objs.items():
                        series_list.append(hash_grouping)
                        series_corr_data = {variable:[], metric_name:[]}
                        hash_data = []
                        for var_value in sorted(var_values.keys(), cmp=_compare):
                            metric_values = var_values[var_value]
                            if var_value not in labels:
                                labels.append(var_value)
                            hash_data.append(metric_values['value'])
                            try:
                                series_corr_data[variable].append(float(var_value))
                            except Exception:
                                series_corr_data[variable].append(var_value)
                            series_corr_data[metric_name].append(metric_values['value'])
                        data.append(hash_data)

                        # calculate correclation coefficent for the series
                        series_df = pandas.DataFrame(data=series_corr_data)
                        try:
                            series_corr, series_p = stats.pearsonr(series_df[variable], series_df[metric_name])
                            
                            if hash_grouping not in corr_data:
                                corr_data[hash_grouping] = []
                            if not numpy.isnan(series_corr):
                                corr_data[hash_grouping].append((series_corr, series_p))
                            else:
                                corr_data[hash_grouping].append((0, 1.0))
                        except Exception:
                            pass

                        overall_corr_data[variable].extend(series_corr_data[variable])
                        overall_corr_data[metric_name].extend(series_corr_data[metric_name])

                    # calculate overal correlation for entire series
                    overall_df = pandas.DataFrame(data=overall_corr_data)
                    try:
                        overall_corr, overall_p = stats.pearsonr(overall_df[variable], overall_df[metric_name])
                        if 'Overall' not in corr_data:
                            corr_data['Overall'] = []
                        if not numpy.isnan(overall_corr):
                            corr_data['Overall'].append((overall_corr, overall_p))
                        else:
                            corr_data['Overall'].append((0.0, 1.0))
                    except Exception:
                        pass

                    if variable not in graphs:
                        graphs[variable] = {}
                    if group_name not in graphs[variable]:
                        graphs[variable][group_name] = {}
                    graphs[variable][group_name][metric_name] = {'labels': labels,
                                    'data': data, 'series': series_list, 'type': 'line',
                                    'options':{
                                        'title': {
                                        'display': True,
                                        'text': metric_name
                                        },
                                        'responsive': True,
                                        'elements':{ 'line': {'fill':False}},
                                        'legend': {
                                            'display': False
                                        }
                                    },
                                    'options_big':{
                                        'title': {
                                        'display': True,
                                        'text': metric_name
                                        },
                                        'responsive': True,
                                        'elements':{ 'line': {'fill':False}},
                                        'legend': {
                                            'display': True,
                                            'position': 'left'
                                        }
                                    }
                    }

                if variable not in correlations:
                    correlations[variable] = {}
                if group_name not in correlations[variable]:
                    correlations[variable][group_name] = {}
                correlations[variable][group_name]['headers'] = corr_headers
                correlations[variable][group_name]['data'] = corr_data

        return {'graphs': graphs, 'data': new_data, 'correlations': correlations}
