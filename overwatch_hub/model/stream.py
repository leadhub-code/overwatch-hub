import logging
import simplejson as json
import sys
from sys import intern
from time import time
from uuid import uuid4

from ..util import intern_keys, serialize_json, deserialize_json

from .errors import ModelDeserializeError
from .stream_helpers import generate_stream_id, flatten_snapshot
from .stream_item import StreamItem


logger = logging.getLogger(__name__)


class Stream:

    def __init__(self, label, on_stream_updated):
        self.id = generate_stream_id(label)
        self.label = label
        self.snapshot_dates = []
        self.items = {} # path -> StreamItem
        self._on_stream_updated = on_stream_updated

    def __repr__(self):
        return '<{cls} {s.id} {s.label!r}>'.format(
            cls=self.__class__.__name__,
            s=self)

    def serialize(self, write):
        write(b'Stream\n')
        write(serialize_json({
            'id': self.id,
            'label': self.label,
            'snapshot_dates': self.snapshot_dates,
        }, check=True))
        for path, stream_item in sorted(self.items.items()):
            write(b'-item\n')
            write(serialize_json({'path': path}))
            stream_item.serialize(write)
        write(b'/Stream\n')

    @classmethod
    def revive(cls, read, on_stream_updated):
        stream = cls(label={}, on_stream_updated=on_stream_updated)
        stream.deserialize(read)
        return stream

    def deserialize(self, readline):
        if readline() != b'Stream\n': raise ModelDeserializeError()
        data = deserialize_json(readline())
        self.label = data['label']
        self.id = data['id']
        self.snapshot_dates = data['snapshot_dates']
        while True:
            line = readline()
            if line == b'/Stream\n':
                break
            elif line == b'-item\n':
                item_data = deserialize_json(readline())
                item_path = tuple(item_data['path'])
                stream_item = StreamItem.revive(readline)
                self.items[item_path] = stream_item
            else:
                raise ModelDeserializeError('Line: {!r}'.format(line))

    def _get_stream_item(self, path):
        assert isinstance(path, tuple)
        if path not in self.items:
            self.items[path] = StreamItem()
        return self.items[path]

    def add_datapoint(self, timestamp_ms, snapshot):
        '''
        Add datapoint to this stream

        Example:

            stream.add_datapoint(
                timestamp_ms=1511346030123,
                snapshot=yaml.load("""
                    foo: bar
                    response:
                        __value: 200
                        __check:
                            state: green
                    watchdog:
                        __watchdog:
                            deadline: 1511346090000
                """))
        '''
        assert isinstance(timestamp_ms, int)
        snapshot_items = flatten_snapshot(snapshot)
        self.snapshot_dates.append(timestamp_ms)
        for path, item_data in snapshot_items.items():
            stream_item = self._get_stream_item(path)
            stream_item.add_snapshot(
                timestamp_ms,
                value=item_data.get('value'),
                check=item_data.get('check'),
                watchdog=item_data.get('watchdog'))
        for path, stream_item in self.items.items():
            if path not in snapshot_items:
                stream_item.add_snapshot(
                    timestamp_ms,
                    value=None,
                    check=None,
                    watchdog=None)
        self._on_stream_updated.fire({
            'stream': self,
        })

    def get_current_checks(self):
        return {path: stream_item.current_check for path, stream_item in self.items.items() if stream_item.current_check}

    def get_current_watchdogs(self):
        return {path: stream_item.current_watchdog for path, stream_item in self.items.items() if stream_item.current_watchdog}
