from flask import Blueprint, Response


bp = Blueprint('api', __name__)


@bp.route('/')
def index():
    return Response('Hello! This is overwatch-hub.', mimetype='text/plain')
