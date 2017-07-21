from collections import namedtuple
import multiprocessing
from pytest import fixture
import requests
from time import sleep
import yaml

from overwatch_hub import get_app


@fixture
def app_process(tmp_dir, db, db_port, get_free_tcp_port):
    app_port = get_free_tcp_port()
    cfg_path = tmp_dir / 'hub-configuration.yaml'
    _write_app_conf(cfg_path, db_port, db.name)
    app = get_app(cfg_path)

    def run_app():
        app.run(debug=False, use_reloader=False, port=app_port)

    p = multiprocessing.Process(name='app', target=run_app)
    try:
        p.start()
        print('Started test server pid {}; it should bind port {}'.format(p.pid, app_port))
        sleep(.01)
        assert p.is_alive()

        r = requests.get('http://127.0.0.1:{port}/'.format(port=app_port))
        print(r.status_code, r.content[:1000])
        assert r.status_code == 200
        assert p.is_alive()

        yield _AppProcess(p, app_port)

    finally:
        if p.is_alive():
            print('Terminating test server {}'.format(p.pid))
            p.terminate()
            p.join()
            assert not p.is_alive()
            print('Test server pid {} finished'.format(p.pid))


_AppProcess =  namedtuple('_AppProcess', 'process port')


def _write_app_conf(cfg_path, db_port, db_name):
    cfg_path.write_text(yaml.dump({
        'overwatch_hub': {
            'mongo': {
                'uri': 'mongodb://127.0.0.1:{port}/'.format(port=db_port),
                'db_name': db_name,
            },
        },
    }))


def test_report(app_process):
    print(app_process)
    assert 0
