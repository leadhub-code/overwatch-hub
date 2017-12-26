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


def sha256_b64(data):
    assert isinstance(data, bytes)
    h = hashlib.sha256(data).digest()
    return urlsafe_b64encode(h).rstrip(b'=').decode()
