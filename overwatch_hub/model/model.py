import logging
from time import time

from .custom_checks import CustomChecks
from .streams import Streams


logger = logging.getLogger(__name__)


class Model:

    def __init__(self):
        self.streams = Streams()
        self.custom_checks = CustomChecks()

    def add_datapoint(self, label, date, snapshot):
        assert isinstance(date, int)
        stream = self.streams.get_or_create_by_label(label)
        logger.info('Adding datapoint stream: %s date: %r', stream.id, date)
        stream.add_datapoint(date, snapshot)
        self.custom_checks.check_stream(stream)

    def add_custom_check(self, **kwargs):
        ch = self.custom_checks.add_custom_check(**kwargs)
        for stream in self.streams.get_all():
            ch.check_stream(stream)
        return ch

    def check_watchdogs(self, now_date=None):
        if not now_date:
            now_date = int(time() * 1000)
        assert isinstance(now_date, int)
        for stream in self.streams.get_all():
            stream.check_watchdogs(now_date)

    def serialize(self):
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
