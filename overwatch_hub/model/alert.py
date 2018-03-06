from copy import deepcopy
import logging

from ..util import sha256_b64, serialize_json, deserialize_json

from .errors import ModelDeserializeError


logger = logging.getLogger(__name__)


class Alert:
    '''
    Attribute is_active means that the watchdog/check is still triggered.

    Alert can be closed by user action even through it is still active.
    '''

    __slots__ = ('_data', '_system', '_update_callback')

    def __init__(self, data, system, update_callback):
        '''
        Private constructor - use Alert.create() or Alert.revive()
        '''
        assert data['id']
        assert data['alert_type'] in {'check', 'watchdog'}
        assert data['severity'] in {'red', 'yellow'}
        assert isinstance(data['path'], tuple)
        self._data = data
        self._system = system
        self._update_callback = update_callback

    id           = property(lambda self: self._data['id'])
    alert_type   = property(lambda self: self._data['alert_type'])
    severity     = property(lambda self: self._data['severity'])
    stream_id    = property(lambda self: self._data['stream_id'])
    stream_label = property(lambda self: deepcopy(self._data['stream_label']))
    path         = property(lambda self: self._data['path'])
    deactivated_time_ms = property(lambda self: self._data['deactivated_time_ms'])
    closed_time_ms      = property(lambda self: self._data['closed_time_ms'])

    def __repr__(self):
        return '<{cls} {s._data}>'.format(cls=self.__class__.__name__, s=self)

    def serialize(self, write):
        write(b'Alert\n')
        write(serialize_json(self._data))
        write(b'/Alert\n')

    @classmethod
    def create(cls, alert_type, severity, stream_id, stream_label, path, system, update_callback):
        return cls(
            system=system,
            update_callback=update_callback,
            data={
                'id': generate_alert_id(system.time_ms(), severity, stream_id, path),
                'alert_type': alert_type,
                'severity': severity,
                'stream_id': stream_id,
                'stream_label': stream_label,
                'path': path,
                'deactivated_time_ms': None,
                'closed_time_ms': None,
            })

    @classmethod
    def revive(cls, readline, system, update_callback):
        if readline() != b'Alert\n': raise ModelDeserializeError()
        data = deserialize_json(readline())
        if readline() != b'/Alert\n': raise ModelDeserializeError()
        # fix types that could not be expressed properly in JSON
        data['path'] = tuple(data['path'])
        return cls(
            system=system,
            update_callback=update_callback,
            data=data)

    def is_active(self):
        return self.deactivated_time_ms is None

    def is_open(self):
        return self.closed_time_ms is None

    def deactivate(self):
        if self._data['deactivated_time_ms']:
            raise Exception('already not active')
        now = self._system.time_ms()
        self._data['deactivated_time_ms'] = now
        if not self._data['closed_time_ms']:
            self._data['clsoed_time_ms'] = now
        self._update_callback(self)

    def close(self):
        if self._data['closed_time_ms']:
            raise Exception('already closed')
        now = self._system.time_ms()
        self._data['closed_time_ms'] = now
        self._update_callback(self)


def generate_alert_id(timestamp_ms, severity, stream_id, path):
    src = [str(timestamp_ms), severity, stream_id, '>'.join(path)]
    return 'A' + sha256_b64(':'.join(src).encode())[:15]
