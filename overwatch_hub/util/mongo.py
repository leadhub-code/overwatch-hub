from pathlib import Path
import pymongo
import re


def connect_to_mongodb(mongo_uri, ssl_ca_cert):
    assert isinstance(mongo_uri, str)
    assert mongo_uri.startswith('mongodb://')
    mongo_uri_safe = _strip_password(mongo_uri)
    mc_kwargs = {}
    if ssl_ca_cert:
        assert Path(ssl_ca_cert).is_file(), ssl_ca_cert
        mc_kwargs['ssl_ca_certs'] = str(ssl_ca_cert)
    try:
        client = pymongo.MongoClient(mongo_uri,
            connect=True,
            connectTimeoutMS=3 * 1000,
            serverSelectionTimeoutMS=5 * 1000,
            w='majority',
            appname=__name__.split('.')[0],
            **mc_kwargs)
    except Exception as e:
        raise Exception('Failed to connect to {!r}: {!r}'.format(mongo_uri_safe, e)) from e
    return client


def _strip_password(uri):
    m = re.match(r'^(.+):.*@(.+)$', uri)
    if m:
        return m.group(1) + ':xxx@' + m.group(2)
    else:
        return uri
