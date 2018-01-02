import logging

from ..util import sha256_b64

from .errors import ModelDeserializeError


logger = logging.getLogger(__name__)


class Alert:

    def __init__(self, severity, stream_id, stream_label, path, update_callback):
        assert severity in {'red', 'yellow'}
        assert isinstance(path, tuple)
        self.id = generate_alert_id(severity, stream_id, path)
        self.severity = severity
        self.stream_id = stream_id
        self.stream_label = stream_label
        self.path = path
        self.is_active = True
        self._update_callback = update_callback

    def __repr__(self):
        return '<{cls} {s.severity} stream: {s.stream_id} {s.stream_label!r} path: {s.path!r}>'.format(
            cls=self.__class__.__name__, s=self)

    def deactivate(self):
        if not self.is_active:
            raise Exception('not active')
        self.is_active = False
        self._update_callback(self)


def generate_alert_id(severity, stream_id, path):
    src = [severity, stream_id, '>'.join(path)]
    return 'A' + sha256_b64(':'.join(src).encode())[:15]
