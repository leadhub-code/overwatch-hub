'''
This module contains all entry points to the overwatch_hub:

- WSGI app
- worker main function
'''

from flask import Flask, g
import os
from pathlib import Path
import yaml

from .api import bp as bp_api
from .model import model_from_conf


def get_app(cfg_path=None):
    '''
    Get WSGI (Flask) app
    '''
    cfg_path = Path(cfg_path or os.environ['OVERWATCH_HUB_CONF']).resolve()
    cfg_dir = cfg_path.parent
    with cfg_path.open() as f:
        cfg = yaml.safe_load(f)['overwatch_hub']
    model_factory = lambda: model_from_conf(cfg, cfg_dir)
    _init_model(model_factory)
    app = Flask(__name__)
    _setup_app(app, model_factory)
    return app


def _init_model(model_factory):
    '''
    Create indexes, maybe perform migrations...
    '''
    model = model_factory()
    model.create_indexes()
    model.close()


def _setup_app(app, model_factory):
    '''
    Helper function for get_app
    '''
    app.register_blueprint(bp_api)

    # Why this lazy model creation?
    # Because this code may run in preload process and we do not want to instantiate Model here.
    # Model object must be created later when the app is running in its worker process.
    model = None

    def get_model():
        nonlocal model
        if model is None:
            model = model_factory()
        return model

    @app.before_request
    def before():
        g.model = get_model()


_app = None

def app(*args):
    '''
    For the "global variable" deployment, e.g. FLASK_APP='overwatch_hub:app' flask run
    '''
    global _app
    if _app is None:
        _app = get_app()
    return _app(*args)
