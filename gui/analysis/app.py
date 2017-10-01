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

    # home handler
    app.add_url_rule('/', None, handlers.home_handler)
    app.add_url_rule('/reload', None, handlers.reload_experiments)

    api = Api(app)
    api.add_resource(exp.ExperimentList, '/api/v1/experiments')
    api.add_resource(exp.Experiment, '/api/v1/experiments/<int:experiment_id>')
    api.add_resource(metrics.Metrics,
                     '/api/v1/experiments/<int:experiment_id>/metrics/<path:metric>')
    api.add_resource(data.Data,'/api/v1/data/<int:experiment_id>')

def load_experiment_data(app):
    '''
    Read the experiment config information from disk
    '''
    logging.info('Loading the experiment data ...')
    experiment_config_file = os.path.join(
        app.config['DATA_DIRECTORY'], 'experiments.json')
    with open(experiment_config_file, 'r') as e_file:
        experiments_config = json.loads(e_file.read())

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
        configs.append(config)

    logging.info(
        'Loading the experiment data: Loaded %d experiments', len(configs))

    # add to the config so anyone can access it
    app.config['EXPERIMENT_LIST'] = configs
