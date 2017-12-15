import logging
import simplejson as json

from ..util import json_dumps_compact

from .errors import ModelDeserializeError


logger = logging.getLogger(__name__)


class StreamItem:

    def __init__(self):
        self.last_date = None
        self.current_value = None
        self.current_check = None
        self.current_watchdog = None
        self.value_history = {}
        self.check_history = {}
        self.watchdog_history = {}

    def serialize(self, write):
        write(b'StreamItem')
        data = {
            'current_value': self.current_value,
            'current_check': self.current_check,
            'current_watchdog': self.current_watchdog,
            'value_history': sorted(self.value_history.items()),
            'check_history': sorted(self.check_history.items()),
            'watchdog_history': sorted(self.watchdog_history.items()),
        }
        write(json_dumps_compact(data).encode())
        write(b'/StreamItem')

    @classmethod
    def revive(self, read):
        stream_item = StreamItem()
        stream_item.deserialize(read)
        return stream_item

    def deserialize(self, read):
        if read() != b'StreamItem':
            raise ModelDeserializeError()
        data = json.loads(read().decode())
        if read() != b'/StreamItem':
            raise ModelDeserializeError()
        self.current_value = data['current_value']
        self.current_check = data['current_check']
        self.current_watchdog = data['current_watchdog']
        self.value_history = dict(data['value_history'])
        self.check_history = dict(data['check_history'])
        self.watchdog_history = dict(data['watchdog_history'])

    def add_snapshot(self, timestamp_ms, value, check, watchdog):
        if not self.last_date or timestamp_ms >= self.last_date:
            self.last_date = timestamp_ms
            self.current_value = value
            self.current_check = check
            self.current_watchdog = watchdog
        if value is not None:
            self.value_history[timestamp_ms] = value
        if check:
            self.check_history[timestamp_ms] = check
        if watchdog:
            self.watchdog_history[timestamp_ms] = watchdog
