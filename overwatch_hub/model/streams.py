import logging

from ..util import ObservableEvent

from .errors import ModelDeserializeError
from .stream import Stream
from .stream_helpers import serialize_label


logger = logging.getLogger(__name__)


class Streams:
    '''
    Collection of Stream objects
    '''

    def __init__(self):
        self._by_label = {} # {serialized label: Stream}
        self._by_id = {}
        self.on_stream_updated = ObservableEvent()

    def serialize(self, write):
        write(b'Streams\n')
        for stream_id, stream in sorted(self._by_id.items()):
            write(b'-stream\n')
            stream.serialize(write)
        write(b'/Streams\n')

    def deserialize(self, readline):
        if readline() != b'Streams\n':
            raise ModelDeserializeError()
        while True:
            line = readline()
            if line == b'/Streams\n':
                break
            elif line == b'-stream\n':
                stream = Stream.revive(readline,
                    on_stream_updated=self.on_stream_updated)
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
            stream = Stream(
                label=label,
                on_stream_updated=self.on_stream_updated)
            self._by_id[stream.id] = stream
            self._by_label[sl] = stream
        return self._by_label[sl]

    def get_all(self):
        '''
        Return all streams
        '''
        return list(self._by_id.values())

    def get_by_id(self, stream_id):
        return self._by_id[stream_id]
