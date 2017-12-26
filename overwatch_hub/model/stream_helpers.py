import logging
from sys import intern

from ..util import json_dumps_compact, sha256_b64, intern_keys


logger = logging.getLogger(__name__)


def serialize_label(label):
    assert isinstance(label, dict)
    return json_dumps_compact(sorted(label.items()))


assert serialize_label({'foo': 'bar'}) == '[["foo","bar"]]'


def generate_stream_id(label):
    r = serialize_label(label).encode()
    h = sha256_b64(r).replace('-', '').replace('_', '')
    return 'S' + h[:15]


assert generate_stream_id({'foo': 'bar'}) == 'STYFHh3z29EPT8mC'


def flatten_snapshot(snapshot):
    assert isinstance(snapshot, dict)
    s_check = intern('check')
    s_watchdog = intern('watchdog')
    s_value = intern('value')
    nodes_by_path = {}

    def get_node(path):
        assert isinstance(path, tuple)
        if path not in nodes_by_path:
            nodes_by_path[path] = {}
        return nodes_by_path[path]

    def r(path, obj):
        if isinstance(obj, dict):
            if obj.get('__check'):
                get_node(path)[s_check] = intern_keys(obj['__check'])

            if obj.get('__watchdog'):
                get_node(path)[s_watchdog] = intern_keys(obj['__watchdog'])

            if '__value' in obj:
                get_node(path)[s_value] = intern_keys(obj['__value'])

            for k, v in obj.items():
                if k.startswith('__'):
                    continue
                r(path + (intern(k), ), v)
        else:
            get_node(path)[s_value] = obj

    r(tuple(), snapshot)
    return nodes_by_path


assert flatten_snapshot({'foo': 'bar'}) == {('foo',): {'value': 'bar'}}
