# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Main application setup
'''
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
    register_resources(app)
    return app


def register_resources(app):
    """Register Flask blueprints."""
    import analysis.resources.home
    import analysis.resources.api.files

    # home handler
    app.add_url_rule('/', None, analysis.resources.home.home_handler)

    api = Api(app)
    api.add_resource(analysis.resources.api.files.FileList, '/api/v1/files')
    #api.register_resource(SingleQuote, '/quote/<int:id>')
