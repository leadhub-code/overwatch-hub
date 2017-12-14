import logging
from time import time
from uuid import uuid4

from ..util import intern_keys

from .snapshot_helpers import snapshot_to_items
from .snapshot_helpers import insert_point_to_history_items
from .snapshot_helpers import retrieve_point_from_history_items

from .stream import Stream


logger = logging.getLogger(__name__)


class Streams:

    def __init__(self):
        self._by_label = {} # serialized label -> Series
        self._by_id = {}

    def get_or_create_by_label(self, label):
        sl = _serialize_label(label)
        if sl not in self._by_label:
            stream = Stream(label)
            self._by_label[sl] = stream
            self._by_id[stream.id] = stream
        return self._by_label[sl]

    def get_all(self):
        return list(self._by_id.values())

    def get_by_id(self, stream_id):
        return self._by_id[stream_id]

    '''
    def serialize(self):
        return [stream.serialize() for stream in self._by_id.values()]

    @classmethod
    def deserialize(cls, data):
        assert isinstance(data, list)
        streams = cls()
        for stream_data in data:
            stream = Stream.deserialize(stream_data)
            streams._by_label[_serialize_label(stream.label)] = stream
            streams._by_id[stream.id] = stream
        return streams
    '''


def _serialize_label(label):
    assert isinstance(label, dict)
    return tuple(sorted(label.items()))
