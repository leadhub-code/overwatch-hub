from collections import namedtuple
import multiprocessing
from pytest import fixture
import requests
import subprocess
from time import sleep
import yaml

from overwatch_hub import get_app


@fixture
def app_process(tmp_dir, db, db_port, get_free_tcp_port):
    app_port = get_free_tcp_port()
    cfg_path = tmp_dir / 'hub-configuration.yaml'
    _write_app_conf(cfg_path, db_port, db.name)

    started = multiprocessing.Event()
    p = multiprocessing.Process(name='app', target=_run_app, args=(cfg_path, app_port, started))
    try:
        p.start()
        print('Started test server pid {}; it should bind port {}'.format(p.pid, app_port))
        started.wait(5)
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


def _run_app(cfg_path, port, started):
    app = get_app(cfg_path)
    started.set()
    app.run(debug=False, use_reloader=False, port=port)


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


def test_run_example_agent(app_process, project_dir):
    agent_path = project_dir / 'scripts/example_agent.py'
    subprocess.check_call(
        [str(agent_path), '--url', 'http://127.0.0.1:{port}/report'.format(port=app_process.port)])
