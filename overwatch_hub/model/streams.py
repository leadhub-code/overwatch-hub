import logging

from .errors import ModelDeserializeError
from .stream import Stream
from .stream_helpers import serialize_label


logger = logging.getLogger(__name__)


class Streams:

    def __init__(self):
        self._by_label = {} # serialized label -> Series
        self._by_id = {}

    def serialize(self, write):
        write(b'Streams')
        for stream in self._by_id.values():
            write(b'-stream')
            stream.serialize(write)
        write(b'/Streams')

    def deserialize(self, read):
        if read() != b'Streams':
            raise ModelDeserializeError()
        while True:
            x = read()
            if x == b'/Streams':
                break
            elif x == b'-stream':
                stream = Stream.revive(read)
                self._by_id[stream.id] = stream
                self._by_label[serialize_label(stream.label)] = stream
            else:
                raise ModelDeserializeError()

    def add_datapoint(self, label, **kwargs):
        stream = self.get_or_create_by_label(label)
        stream.add_datapoint(**kwargs)

    def get_or_create_by_label(self, label):
        sl = serialize_label(label)
        if sl not in self._by_label:
            stream = Stream(label)
            self._by_id[stream.id] = stream
            self._by_label[sl] = stream
        return self._by_label[sl]

    def get_all(self):
        return list(self._by_id.values())

    def get_by_id(self, stream_id):
        return self._by_id[stream_id]
