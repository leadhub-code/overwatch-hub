import logging
from pathlib import Path
from pytest import fixture
import sys
from instant_mongo import InstantMongoDB
from instant_mongo.port_guard import PortGuard


logging.basicConfig(
    format='~ %(asctime)s [%(process)d] %(name)s %(levelname)5s: %(message)s',
    level=logging.DEBUG,
    stream=sys.stdout)

logging.getLogger('instant_mongo').setLevel(logging.INFO)


@fixture
def tmp_dir(tmpdir):
    return Path(str(tmpdir))


@fixture
def get_free_tcp_port():
    pg = PortGuard(start_port=9000)
    try:
        yield lambda: pg.get_available_port()
    finally:
        pg.close()


@fixture
def db(instant_mongodb):
    return instant_mongodb.get_new_test_db()


@fixture
def db_port(instant_mongodb):
    assert instant_mongodb.port
    return instant_mongodb.port


@fixture(scope='session')
def instant_mongodb(tmpdir_factory):
    temp_dir = tmpdir_factory.mktemp('instant-mongo')
    with InstantMongoDB(data_parent_dir=temp_dir) as im:
        yield im


@fixture
def model(db):
    from overwatch_hub.model import Model
    m = Model(db=db)
    m.create_indexes()
    return m
