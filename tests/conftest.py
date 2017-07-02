import logging
from pytest import fixture
from instant_mongo import InstantMongoDB


logging.basicConfig(
    format='~ %(name)s %(levelname)5s: %(message)s',
    level=logging.DEBUG)

logging.getLogger('instant_mongo').setLevel(logging.INFO)


@fixture
def db(instant_mongodb):
    return instant_mongodb.get_new_test_db()


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
