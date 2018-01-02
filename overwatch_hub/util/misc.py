import hashlib
from base64 import urlsafe_b64encode
import simplejson as json
from sys import intern


def intern_keys(d):
    if not isinstance(d, dict):
        return d
    r = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = intern_keys(v)
        if isinstance(k, str):
            k = intern(k)
        r[k] = v
    return r


def json_dumps_compact(obj):
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=True,
        separators=(',', ':'))


def serialize_json(obj, check=False):
    assert isinstance(obj, dict)
    data = json_dumps_compact(obj).encode()
    assert b'\n' not in data
    if check:
        deserialized_obj = deserialize_json(data)
        if deserialized_obj != obj:
            raise Exception('Serialization error: {!r} != {!r}'.format(deserialized_obj, obj))
    return data + b'\n'


def deserialize_json(data):
    assert isinstance(data, bytes)
    data = data.strip()
    if not data.startswith(b'{') or not data.endswith(b'}'):
        raise Exception('Invalid format')
    return json.loads(data.decode())


def sha256_b64(data):
    assert isinstance(data, bytes)
    h = hashlib.sha256(data).digest()
    return urlsafe_b64encode(h).rstrip(b'=').decode()
