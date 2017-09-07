# -*- coding: utf-8 -*-
'''
Updated on September, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Basic http handlers
'''
from flask import send_file, current_app, redirect, url_for
from analysis.app import load_experiment_data


def home_handler():
    '''
    Home handler, Return landing page
    '''
    return send_file('static/index.html')

def reload_experiments():
    '''
    Reload the experiment data
    '''
    load_experiment_data(current_app)
    return redirect(url_for('home_handler'))
