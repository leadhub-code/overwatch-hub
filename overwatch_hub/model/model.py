import logging
from time import time

from .custom_checks import CustomChecks
from .streams import Streams


logger = logging.getLogger(__name__)


class Model:

    def __init__(self):
        self.streams = Streams()
        self.custom_checks = CustomChecks()
        self.custom_checks.subscribe_custom_check_added(self._on_custom_check_added)

    def _on_custom_check_added(self, custom_check):
        for stream in self.streams.get_all():
            custom_check.check_stream(stream)
        

    def add_datapoint(self, label, date, snapshot):
        assert isinstance(date, int)
        stream = self.streams.get_or_create_by_label(label)
        logger.info('Adding datapoint stream: %s date: %r', stream.id, date)
        stream.add_datapoint(date, snapshot)
        self.custom_checks.check_stream(stream)

    def add_custom_check(self, **kwargs):
        ch = self.custom_checks.add_custom_check(**kwargs)

    def check_watchdogs(self, now_date=None):
        if not now_date:
            now_date = int(time() * 1000)
        assert isinstance(now_date, int)
        for stream in self.streams.get_all():
            stream.check_watchdogs(now_date)

    def serialize(self, acc):
        acc(b'Model')
        self.streams.se
        acc(b'/Model')
        return {
            'streams': self.streams.serialize(),
            'custom_checks': self.custom_checks.serialize(),
        }

    @classmethod
    def deserialize(cls, data):
        model = cls()
        model.streams = Streams.deserialize(data['streams'])
        model.custom_checks = CustomChecks.deserialize(data['custom_checks'])
        return model
