import logging
import os
from pathlib import Path
import yaml


logger = logging.getLogger(__name__)


class Configuration:

    def __init__(self, cfg_path):
        cfg_path = Path(cfg_path)
        base_path = cfg_path.parent
        data = yaml.safe_load(cfg_path.read_text())['overwatch_hub']
        self.report_tokens = set()
        if data.get('report_tokens'):
            if not isinstance(data['report_tokens'], list):
                raise Exception('report_tokest must be list')
            self.report_tokens = set(data['report_tokens'])
        if data.get('client_tokens'):
            if not isinstance(data['client_tokens'], list):
                raise Exception('report_tokest must be list')
            self.client_tokens = set(data['client_tokens'])
        self.http_interface = _HTTPInterface(data.get('http_interface'))
        self.log = _Log(data.get('log'), base_path)


class _HTTPInterface:

    def __init__(self, data):
        self.bind_host = 'localhost'
        self.bind_port = 8090
        if data:
            if 'bind_host' in data:
                self.bind_host = data['bind_host']
            if data.get('bind_port'):
                self.bind_port = int(data['bind_port'])

    def get_bind_host(self):
        if 'OVERWATCH_HUB_BIND_HOST' in os.environ:
            return os.environ['OVERWATCH_HUB_BIND_HOST']
        return self.bind_host

    def get_bind_port(self):
        if 'OVERWATCH_HUB_BIND_PORT' in os.environ:
            return int(os.environ['OVERWATCH_HUB_BIND_PORT'])
        return self.bind_port


class _Log:

    def __init__(self, data, base_path):
        self.file_path = None
        if data:
            if data.get('file'):
                self.file_path = base_path / data['file']
