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
    print('data:')
    pprint(data)
    date = parse_date(data['date'])
    g.model.store_state(
        data['agent_token'], data.get('series_id'), date,
        data['tags'], data['values'], request.remote_addr)
    return jsonify({"ok": True})


@bp.route('/current-states')
def current_states():
    states = []
    series_by_id = {doc['_id']: doc for doc in g.model._c_series.find()}
    for cs_doc in g.model._c_current_states.find():
        cs_series = series_by_id[cs_doc['series_id']];
        states.append({
            #'_raw_doc': repr(cs_doc),
            'agent': {
                'internal_id': str(cs_doc['agent_id']),
            },
            'series': {
                'internal_id': str(cs_doc['series_id']),
                'id': cs_series['external_id'],
            },
            'date': cs_doc['date'].isoformat() + 'Z',
            'tags': cs_doc['tags'],
            'values': cs_doc['values'],
            'remote_addr': cs_doc['remote_addr'],
        })
    return jsonify({'current_states': states})


def parse_date(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
