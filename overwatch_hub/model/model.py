from io import BytesIO
import logging
from time import time

from .alerts import Alerts
from .errors import ModelDeserializeError
from .custom_checks import CustomChecks
from .streams import Streams


logger = logging.getLogger(__name__)


class Model:

    def __init__(self):
        self.streams = Streams()
        self.alerts = Alerts()
        #self.custom_checks = CustomChecks()
        #self.custom_checks.subscribe_custom_check_added(self._on_custom_check_added)

    def _on_custom_check_added(self, custom_check):
        for stream in self.streams.get_all():
            custom_check.check_stream(stream)

    def add_custom_check(self, **kwargs):
        ch = self.custom_checks.add_custom_check(**kwargs)

    def check_watchdogs(self, now_date=None):
        if not now_date:
            now_date = int(time() * 1000)
        assert isinstance(now_date, int)
        for stream in self.streams.get_all():
            stream.check_watchdogs(now_date)

    def serialize(self, write=None):
        if write is None:
            f = BytesIO()
            def write(data):
                f.write(data)
                f.write(b'\n')
            self.serialize(write)
            return f.getvalue()
        write(b'Model')
        write(b'-streams')
        self.streams.serialize(write)
        write(b'-alerts')
        self.alerts.serialize(write)
        write(b'/Model')

    @classmethod
    def revive(cls, src):
        if isinstance(src, bytes):
            f = BytesIO(src)
            read = lambda: f.readline().rstrip()
        elif callable(src):
            read = src
        elif hasattr(src, 'readline'):
            read = lambda: src.readline().rstrip()
        else:
            raise Exception('Parameter read must be bytes or callable')
        m = cls()
        m.deserialize(read)
        return m

    def deserialize(self, read):
        if read() != b'Model': raise ModelDeserializeError()
        if read() != b'-streams': raise ModelDeserializeError()
        self.streams.deserialize(read)
        if read() != b'-alerts': raise ModelDeserializeError()
        self.alerts.deserialize(read)
        if read() != b'/Model': raise ModelDeserializeError()
