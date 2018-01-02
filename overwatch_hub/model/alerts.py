import logging

from .errors import ModelDeserializeError


logger = logging.getLogger(__name__)


class Alerts:

    def __init__(self):
        self.all_alerts = {} # alert id -> alert
        self.active_alerts = {}  # alert id -> alert

    def serialize(self, write):
        write(b'Alerts\n')
        write(b'/Alerts\n')

    def deserialize(self, read):
        if read() != b'Alerts\n':
            raise ModelDeserializeError()
        if read() != b'/Alerts\n':
            raise ModelDeserializeError()

    def get_active_alerts(self, stream_id):
        return [a for a in self.active_alerts.values() if a.stream_id == stream_id]
