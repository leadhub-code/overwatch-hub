from datetime import datetime
from flask import Blueprint, Response, request, jsonify, g
from pprint import pprint


bp = Blueprint('api', __name__)


@bp.route('/')
def index():
    return Response('Hello! This is overwatch-hub.', mimetype='text/plain')


@bp.route('/report', methods=['POST'])
def report():
    data = request.get_json()
    if not data:
        raise Exception('No data')
    print('data:')
    pprint(data)
    date = parse_date(data['date'])
    g.model.store_state(
        data['agent_token'], data.get('series_id'), date,
        data['tags'], data['values'], request.remote_addr)
    return jsonify({"ok": True})


def parse_date(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
