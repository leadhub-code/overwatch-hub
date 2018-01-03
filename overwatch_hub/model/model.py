from io import BytesIO
import logging
from time import time

from .alert_manager import AlertManager
from .alerts import Alerts
from .errors import ModelDeserializeError
from .custom_checks import CustomChecks
from .streams import Streams
from .system import System


logger = logging.getLogger(__name__)


class Model:

    def __init__(self, system=None):
        self.system = system or System()
        self.streams = Streams()
        self.alerts = Alerts()
        self.alert_manager = AlertManager(alerts=self.alerts, system=self.system)
        self.streams.on_stream_updated.subscribe(self.alert_manager.stream_updated)
        #self.custom_checks = CustomChecks()
        #self.custom_checks.subscribe_custom_check_added(self._on_custom_check_added)

    # def _on_custom_check_added(self, custom_check):
    #     for stream in self.streams.get_all():
    #         custom_check.check_stream(stream)

    #def add_custom_check(self, **kwargs):
    #    ch = self.custom_checks.add_custom_check(**kwargs)

    def check_watchdogs(self):
        for stream in self.streams.get_all():
            self.alert_manager.check_stream(stream)

    # def check_watchdogs(self, now_date=None):
    #     if not now_date:
    #         now_date = int(time() * 1000)
    #     assert isinstance(now_date, int)
    #     for stream in self.streams.get_all():
    #         stream.check_watchdogs(now_date)

    def serialize(self, write=None):
        if write is None:
            f = BytesIO()
            self.serialize(f.write)
            return f.getvalue()
        write(b'Model\n')
        write(b'-streams\n')
        self.streams.serialize(write)
        write(b'-alerts\n')
        self.alerts.serialize(write)
        write(b'/Model\n')

    @classmethod
    def revive(cls, src):
        if isinstance(src, bytes):
            f = BytesIO(src)
            readline = f.readline
        elif callable(src):
            readline = src
        elif hasattr(src, 'readline') and callable(src.readline):
            readline = src.readline
        else:
            raise Exception('Parameter src must be bytes or callable')
        m = cls()
        m.deserialize(readline)
        return m

    def deserialize(self, readline):
        if readline() != b'Model\n': raise ModelDeserializeError()
        if readline() != b'-streams\n': raise ModelDeserializeError()
        self.streams.deserialize(readline)
        if readline() != b'-alerts\n': raise ModelDeserializeError()
        self.alerts.deserialize(readline)
        if readline() != b'/Model\n': raise ModelDeserializeError()
