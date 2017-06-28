from flask import Flask

from .api import bp as bp_api


def get_app():
    app = Flask(__name__)
    app.register_blueprint(bp_api)
    return app


_app = None

def app(*args):
    '''
    For the "global variable" deployment, e.g. FLASK_APP='overwatch_hub:app' flask run
    '''
    global _app
    if _app is None:
        _app = get_app()
    return _app(*args)
