from datetime import datetime
from flask import Blueprint, Response, request, jsonify, g
from pprint import pprint


bp = Blueprint('api', __name__)


@bp.route('/')
def index():
    return Response('Hello! This is overwatch-hub.\n', mimetype='text/plain')


@bp.route('/report', methods=['POST'])
def report():
    data = request.get_json()
    if not data:
        raise Exception('No data')
    pprint({'report data': data})

    agent = g.model.agents.get_or_create(
        agent_id=data['agent_id'],
        agent_token=data['agent_token'])









    g.model.accept_state(data, request.remote_addr)
    return jsonify({"ok": True})


@bp.route('/current-states')
def current_states():
    return jsonify({'current_states': g.model.get_current_states()})


def parse_date(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
