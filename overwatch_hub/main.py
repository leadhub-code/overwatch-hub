from flask import Flask, g
import os
from pathlib import Path
import yaml

from .api import bp as bp_api
from .model import model_from_conf


def get_app(cfg_path):
    cfg_path = Path(cfg_path).resolve()
    cfg_dir = cfg_path.parent
    with cfg_path.open() as f:
        cfg = yaml.safe_load(f)['overwatch_hub']
    model = model_from_conf(cfg, cfg_dir)
    model.create_indexes()
    app = Flask(__name__)
    _setup_app(app, model)
    return app


def _setup_app(app, model):
    app.register_blueprint(bp_api)

    @app.before_request
    def before():
        g.model = model


_app = None

def app(*args):
    '''
    For the "global variable" deployment, e.g. FLASK_APP='overwatch_hub:app' flask run
    '''
    global _app
    if _app is None:
        _app = get_app(os.environ['OVERWATCH_HUB_CONF'])
    return _app(*args)
