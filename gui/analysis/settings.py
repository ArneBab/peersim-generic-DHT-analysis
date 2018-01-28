# -*- coding: utf-8 -*-
"""Application configuration."""
import os
from datetime import timedelta


class Config(object):
    """Base configuration."""

    SECRET_KEY = os.environ.get('ANALYSIS_SECRET', 'secret-key-analysis')  
    DEBUG = False
    DATA_DIRECTORY = os.environ.get('DATA_DIR')
