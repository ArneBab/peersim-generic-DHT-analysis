# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Main application setup
'''
import os
import logging
import json
from flask import Flask
from flask_restful import Api

from analysis.settings import Config


def create_app(config_object=Config):
    """An application factory, as explained here:
    http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split('.')[0])
    app.url_map.strict_slashes = False
    app.config.from_object(config_object)
    logging.getLogger().setLevel(logging.INFO)
    register_resources(app)
    load_experiment_data(app)
    return app


def register_resources(app):
    """Register Flask blueprints."""
    import analysis.resources.handlers as handlers
    import analysis.resources.api.experiments as exp
    import analysis.resources.api.metrics as metrics
    import analysis.resources.api.data as data
    import analysis.resources.api.summary.summary as summary
    import analysis.resources.api.summary.csv as csv

    # home handler
    app.add_url_rule('/', None, handlers.home_handler)
    app.add_url_rule('/reload', None, handlers.reload_experiments)

    api = Api(app)
    api.add_resource(exp.ExperimentList, '/api/v1/experiments')
    api.add_resource(exp.Experiment, '/api/v1/experiments/<int:experiment_id>')
    api.add_resource(exp.ExperimentMetrics,
                     '/api/v2/experiments/<int:experiment_id>')
    api.add_resource(metrics.Metrics,
                     '/api/v1/experiments/<int:experiment_id>/metrics/<path:metric>')
    api.add_resource(exp.ExperimentCSV,
                     '/api/v1/experiments/<int:experiment_id>/csv/<path:csv_file>')
    api.add_resource(exp.ExperimentStatic,
                     '/api/v1/experiments/<int:experiment_id>/static/<path:static_file>')
    api.add_resource(data.Data, '/api/v1/data/<int:experiment_id>')

    api.add_resource(summary.Summary, '/api/v1/summary')
    api.add_resource(csv.Csv, '/api/v1/summary/csv')
    api.add_resource(summary.SummaryGraphs,
                     '/api/v1/summary/graphs/<path:variable>')
    api.add_resource(summary.SummaryCorrelations,
                     '/api/v1/summary/correlations/<path:variable>')


def load_experiment_data(app):
    '''
    Read the experiment config information from disk
    '''
    logging.info('Loading the experiment data ...')
    experiment_config_file = os.path.join(
        app.config['DATA_DIRECTORY'], 'experiments.json')
    with open(experiment_config_file, 'r') as e_file:
        experiments_config = json.loads(e_file.read())

    # make the paths absolute
    for exp_files in experiments_config:
        exp_files['config'] = os.path.join(
            app.config['DATA_DIRECTORY'], exp_files['config'])
        exp_files['experiment'] = os.path.join(
            app.config['DATA_DIRECTORY'], exp_files['experiment'])

    # read in each experiment config file
    configs = []
    config_groups = {}
    exp_id = 0

    for exp in experiments_config:
        with open(exp['config'], 'r') as c_file:
            config = json.loads(c_file.read())
            config['id'] = exp_id
            exp_id += 1
            config['self'] = exp['config']
            config['menu_path'] = _clean_path(config['path'])
            config['menu_path_name'] = _clean_path_name(
                config['menu_path'], config['id'])
            configs.append(config)

            if exp['repeat_group'] not in config_groups:
                config_copy = config.copy()
                config_copy.pop('repeat')
                config_copy['self'] = os.path.dirname(config_copy['self'])
                config_copy['path'] = os.path.dirname(config_copy['path'])
                config_groups[exp['repeat_group']] = config_copy

    for config in config_groups.values():
        config['id'] = exp_id
        exp_id += 1
        config['menu_path'] = _clean_path(config['path'], True)
        config['menu_path_name'] = _clean_path_name(
            config['menu_path'], config['id'])

    experiment_hier = {}
    # Build experiment hierarchy before finishing the experiment config list
    for config in config_groups.values():
        key = _clean_path_name(config['menu_path'], None)
        experiment_hier[key] = {'children': [
        ], 'label': config['menu_path_name'], 'data': '/#/experiments/' + str(config['id'])}
    for config in configs:
        group_name = _clean_path_name(_clean_path(config['path'], True), None)
        experiment_hier[group_name]['children'].append(
            {'children': [], 'label': config['menu_path_name'], 'data': '/#/experiments/' + str(config['id'])})
    for exp_hier in experiment_hier.values():
        exp_hier['children'].sort(key=lambda x: x['label'])

    experiment_hier_items = []
    for key in sorted(experiment_hier.keys()):
        experiment_hier_items.append(experiment_hier[key])

    configs.extend(config_groups.values())

    logging.info(
        'Loading the experiment data: Loaded %d experiments', len(configs))

    # add to the config so anyone can access it
    app.config['EXPERIMENT_LIST'] = configs
    app.config['EXPERIMENT_HIERARCHY'] = experiment_hier_items


def _clean_path(path, is_group=False):
    if is_group:
        return path.replace('\\', '/').split('/')[1:-1:2]
    return path.replace('\\', '/').split('/')[1::2]


def _clean_path_name(path_list, id_num):
    menu_path = ':'.join(path_list).lower()
    if id_num is not None:
        menu_path = str(id_num) + ' - ' + menu_path
    return menu_path.replace('dhtrouter', '').replace('random', 'Rand')
