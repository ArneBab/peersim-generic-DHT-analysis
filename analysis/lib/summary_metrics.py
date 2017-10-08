# -*- coding: utf-8 -*-
'''
Updated on October, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Run the final experiment comparisions
'''
import json
from lib.configuration import Configuration

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
