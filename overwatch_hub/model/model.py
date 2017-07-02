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
        self._c_series.create_index([
            ('agent_id', ASC),
            ('external_id', ASC),
        ], unique=True)
        self._c_current_states.create_index('agent_id')
        self._c_current_states.create_index('series_id', unique=True)
        self._c_history_states.create_index([
            ('agent_id', ASC),
            ('series_id', ASC),
            ('date', ASC),
        ])

    def __repr__(self):
        return '<{cls} {s._db!r}>'.format(cls=self.__class__.__name__, s=self)

    def store_state(self, agent_token, series_external_id, date, tags, values, remote_addr):
        assert isinstance(date, datetime)
        if series_external_id is not None and not isinstance(series_external_id, str):
            raise Exception('series_external_id must be None or str')
        if not isinstance(tags, dict):
            raise Exception('tags must be dict')
        if not isinstance(values, dict):
            raise Exception('values must be dict')
        agent_id = self._get_or_create_agent(agent_token)
        series_id = self._get_or_create_series(agent_id, series_external_id)
        assert isinstance(agent_id, ObjectId)
        assert isinstance(series_id, ObjectId)

        self._c_history_states.insert_one({
            'agent_id': agent_id,
            'series_id': series_id,
            'date': date,
            'tags': tags,
            'values': values,
            'remote_addr': remote_addr,
        })

        cs_doc = self._c_current_states.find_one({'series_id': series_id})
        if not cs_doc or cs_doc['date'] < date:
            self._c_current_states.update_one(
                {
                    'series_id': series_id,
                }, {
                    '$set': {
                        'agent_id': agent_id,
                        'date': date,
                        'tags': tags,
                        'values': values,
                        'remote_addr': remote_addr,
                    },
                }, upsert=True)

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

    def _get_or_create_series(self, agent_id, series_external_id):
        assert isinstance(agent_id, ObjectId)
        doc = self._c_series.find_one({'agent_id': agent_id, 'external_id': series_external_id})
        if doc:
            return doc['_id']
        series_id = ObjectId()
        self._c_series.insert_one({
            '_id': series_id,
            'agent_id': agent_id,
            'external_id': series_external_id,
        })
        return series_id
