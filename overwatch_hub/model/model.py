from bson import ObjectId
from datetime import datetime
import pymongo
from pymongo import ASCENDING as ASC
from pymongo.uri_parser import parse_uri

from ..util import connect_to_mongodb


assert pymongo.version > '3.2'


def model_from_conf(cfg, cfg_dir):
    mongo_cfg = cfg['mongo']
    ca_cert_file = None
    if mongo_cfg.get('ssl'):
        if mongo_cfg['ssl'].get('ca_cert_file'):
            ca_cert_file = cfg_dir / mongo_cfg['ssl']['ca_cert_file']
    client = connect_to_mongodb(mongo_cfg['uri'], ca_cert_file)
    db_name = mongo_cfg.get('db_name') or parse_uri(mongo_cfg['uri'])['database']
    db = client[db_name]
    return Model(db)


class Model:

    def __init__(self, db):
        self._c_agents = db['agents']
        self._c_series = db['series']
        self._c_history_states = db['states.history']
        self._c_current_states = db['states.current']

    def create_indexes(self):
        self._c_agents.create_index('token', unique=True)
        self._c_series.create_index(
            [
                ('agent_id', ASC),
                ('name', ASC),
            ],
            unique=True)
        self._c_current_states.create_index('agent_id')
        self._c_history_states.create_index(
            [
                ('agent_id', ASC),
                ('series_id', ASC),
                ('date', ASC),
            ])

    def __repr__(self):
        return '<{cls} {s._db!r}>'.format(cls=self.__class__.__name__, s=self)

    def get_current_states(self):
        current_states = []
        series_by_id = {doc['_id']: doc for doc in self._c_series.find()}
        for cs_doc in self._c_current_states.find():
            cs_series = series_by_id[cs_doc['_id']];
            current_states.append({
                'agent': {
                    'internal_id': str(cs_doc['agent_id']),
                },
                'series': {
                    'internal_id': str(cs_series['_id']),
                    'name': cs_series['name'],
                },
                'date': cs_doc['date'].isoformat() + 'Z',
                'tags': export_tags(cs_doc['tags']),
                'values': cs_doc['values'],
                'remote_addr': cs_doc['remote_addr'],
            })
        return current_states

    def accept_state(self, payload, remote_addr):
        '''
        Doesn't return anything
        '''
        agent_token = payload['agent_token']
        series_name = payload.get('series') or None
        date = preprocess_date(payload['date'])
        tags = preprocess_state_tags(payload['tags'])
        values = preprocess_state_values(payload.get('values'))
        checks = preprocess_state_checks(payload.get('checks'))
        expire_checks = preprocess_state_expire_checks(payload.get('expire_checks'))

        if not isinstance(date, datetime):
            raise Exception('date must be datetime')
        if series_name is not None and not isinstance(series_name, str):
            raise Exception('series must be None or str')

        agent_id = self._get_or_create_agent(agent_token)
        series_id = self._get_or_create_series(agent_id, series_name)
        assert isinstance(agent_id, ObjectId)
        assert isinstance(series_id, ObjectId)

        self._c_history_states.insert_one({
            'agent_id': agent_id,
            'series_id': series_id,
            'date': date,
            'tags': tags,
            'values': values,
            'checks': checks,
            'expire_checks': expire_checks,
            'remote_addr': remote_addr,
        })

        cs_doc = self._c_current_states.find_one({'_id': series_id})
        if not cs_doc or cs_doc['date'] < date:

            # save also as current state
            self._c_current_states.replace_one(
                {
                    '_id': series_id,
                }, {
                    '_id': series_id,
                    'agent_id': agent_id,
                    'date': date,
                    'tags': tags,
                    'values': values,
                    'checks': checks,
                    'expire_checks': expire_checks,
                    'remote_addr': remote_addr,
                },
                upsert=True)


    def _get_or_create_agent(self, agent_token):
        doc = self._c_agents.find_one({'token': agent_token})
        if doc:
            return doc['_id']
        agent_id = ObjectId()
        self._c_agents.insert_one({
            '_id': agent_id,
            'token': agent_token,
        })
        return agent_id


    def _get_or_create_series(self, agent_id, series_name):
        assert isinstance(agent_id, ObjectId)
        doc = self._c_series.find_one({'agent_id': agent_id, 'name': series_name})
        if doc:
            return doc['_id']
        series_id = ObjectId()
        self._c_series.insert_one({
            '_id': series_id,
            'agent_id': agent_id,
            'name': series_name,
        })
        return series_id


def preprocess_date(dt):
    if isinstance(dt, datetime):
        return dt
    if not isinstance(dt, str):
        raise Exception('date must be datetime or str: {!r}'.format(dt))
    return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')


def optional(d):
    return {k: v for k, v in d.items() if v}


def preprocess_state_tags(data):
    tags = []
    if isinstance(data, dict):
        for k, v in sorted(data.items()):
            if not isinstance(k, str):
                raise Exception('Tag keys must be str: {!r}'.format(data))
            tags.append('{}={}'.format(k, v))
    else:
        Exception('State tags must be dict: {!r}'.format(data))
    return tags


def export_tags(tags):
    exp = []
    for tag in tags:
        assert isinstance(tag, str)
        k, v = tag.split('=', 1)
        exp.append({
            'key': k,
            'value': v,
        })
    return exp


def preprocess_state_values(data):
    values = []
    if isinstance(data, dict):
        _preprocess_values_object(values, data)
    elif isinstance(data, list):
        for row in data:
            if not isinstance(key, str):
                raise Exception('key must be str: {!r}'.format(row))
            values.append({
                'key': row['key'],
                'value': row['value'],
                **optional({
                    'unit': row.get('unit'),
                }),
            })
    else:
        raise Exception('State values must be dict or list: {!r}'.format(data))
    return values


def _preprocess_values_object(values, data, path=''):
    if isinstance(data, dict):
        for k, v in sorted(data.items()):
            k = str(k).replace('.', '_')
            _preprocess_values_object(values, v, path=path + '.' + k)
    elif isinstance(data, list):
        for n, v in enumerate(v):
            _preprocess_values_object(values, v, path=path + '.' + str(n))
    else:
        values.append({
            'key': path.lstrip('.'),
            'value': data,
        })


def preprocess_state_checks(data):
    if not data:
        return []
    assert 0, data



def preprocess_state_expire_checks(data):
    if not data:
        return []
    assert 0, data
