from bson import ObjectId
from collections import defaultdict
from datetime import datetime
from pprint import pprint
import re
from textwrap import dedent
import yaml


def test_accept_state_simple(db, model):
    now = datetime.strptime('2017-07-01 12:00', '%Y-%m-%d %H:%M')
    model.accept_state(
        {
            'agent_token': 'at1',
            'series': 's1',
            'date': now.isoformat(),
            'tags': {
                'tk1': 'tv1',
                'tk2': 'tv2',
            },
            'values': {
                'vk1': 'vv1',
                'vk2': {
                    'vk21': 'vv21',
                    'vk22': 'vv22',
                },
            },
        },
        remote_addr='127.0.0.1')

    assert yaml_dump(strip_oids(dump_db(db))) == dedent('''\
        agents:
            oid000:
                _id: oid000
                token: at1
        series:
            oid001:
                _id: oid001
                agent_id: oid000
                name: s1
        states.current:
            oid001:
                _id: oid001
                agent_id: oid000
                checks: []
                date: 2017-07-01 12:00:00
                expire_checks: []
                remote_addr: 127.0.0.1
                tags:
                - tk1=tv1
                - tk2=tv2
                values:
                -   key: vk1
                    value: vv1
                -   key: vk2.vk21
                    value: vv21
                -   key: vk2.vk22
                    value: vv22
        states.history:
            oid002:
                _id: oid002
                agent_id: oid000
                checks: []
                date: 2017-07-01 12:00:00
                expire_checks: []
                remote_addr: 127.0.0.1
                series_id: oid001
                tags:
                - tk1=tv1
                - tk2=tv2
                values:
                -   key: vk1
                    value: vv1
                -   key: vk2.vk21
                    value: vv21
                -   key: vk2.vk22
                    value: vv22
    ''')

    assert strip_oids(model.get_current_states()) == [
        {'agent': {'internal_id': 'oid000|str'},
         'series': {'internal_id': 'oid001|str', 'name': 's1'},
         'date': '2017-07-01T12:00:00Z',
         'remote_addr': '127.0.0.1',
         'tags': [{'key': 'tk1', 'value': 'tv1'},
                  {'key': 'tk2', 'value': 'tv2'}],
         'values': [{'key': 'vk1', 'value': 'vv1'},
                    {'key': 'vk2.vk21', 'value': 'vv21'},
                    {'key': 'vk2.vk22', 'value': 'vv22'}]}]


def strip_oids(obj):
    m = defaultdict(lambda: 'oid{:03d}'.format(len(m)))
    def r(obj):
        if isinstance(obj, ObjectId):
            return m[str(obj)]
        if isinstance(obj, str) and re.match(r'^[0-9a-f]{24}$', obj):
            return m[obj] + '|str'
        if isinstance(obj, dict):
            return {r(k): r(v) for k, v in sorted(obj.items())}
        if isinstance(obj, list):
            return [r(v) for v in obj]
        return obj

    return r(obj)


def yaml_dump(obj):
    return yaml.dump(obj, indent=4, default_flow_style=False)


def dump_db(db):
    return {cn: dump_collection(db[cn]) for cn in db.collection_names()}


def dump_collection(c):
    return {doc['_id']: doc for doc in c.find()}
