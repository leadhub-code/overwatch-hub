import logging

from ..util import sha256_b64

from .errors import ModelDeserializeError


logger = logging.getLogger(__name__)


class Alert:

    '''
    Attribute is_active means that the watchdog/check is still triggered.

    Alert can be closed by user action even through it is still active.
    '''

    def __init__(self, system, alert_type, severity, stream_id, stream_label, path, update_callback):
        assert alert_type in {'check', 'watchdog'}
        assert severity in {'red', 'yellow'}
        assert isinstance(path, tuple)
        self._system = system
        self.alert_type = alert_type
        self.id = generate_alert_id(self._system.time_ms(), severity, stream_id, path)
        self.severity = severity
        self.stream_id = stream_id
        self.stream_label = stream_label
        self.path = path
        self.deactivated_time_ms = None
        self.closed_time_ms = None
        self._update_callback = update_callback

    def is_active(self):
        return self.deactivated_time_ms is None

    def is_open(self):
        return self.closed_time_ms is None

    def __repr__(self):
        return '<{cls} {s.id} {s.alert_type} {s.severity} stream: {s.stream_id} {s.stream_label!r} path: {s.path!r}>'.format(
            cls=self.__class__.__name__, s=self)

    def deactivate(self):
        if self.deactivated_time_ms:
            raise Exception('already not active')
        now = self._system.time_ms()
        self.deactivated_time_ms = now
        if not self.closed_time_ms:
            self.clsoed_time_ms = now
        self._update_callback(self)

    def close(self):
        if self.closed_time_ms:
            raise Exception('already closed')
        now = self._system.time_ms()
        self.clsoed_time_ms = now
        self._update_callback(self)


def generate_alert_id(timestamp_ms, severity, stream_id, path):
    src = [str(timestamp_ms), severity, stream_id, '>'.join(path)]
    return 'A' + sha256_b64(':'.join(src).encode())[:15]
