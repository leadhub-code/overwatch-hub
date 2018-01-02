import logging

from .alert import Alert
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

    def create_alert(self, severity, stream_id, stream_label, path):
        alert = Alert(
            severity=severity,
            stream_id=stream_id,
            stream_label=stream_label,
            path=path,
            update_callback=self._alert_updated)
        assert alert.id not in self.all_alerts
        self.all_alerts[alert.id] = alert
        self._alert_updated(alert)

    def _alert_updated(self, alert):
        assert alert.id in self.all_alerts
        if alert.is_active:
            self.active_alerts[alert.id] = alert
        else:
            self.active_alerts.pop(alert.id, None)
