import logging

from .alert import Alert
from .errors import ModelDeserializeError


logger = logging.getLogger(__name__)


class Alerts:

    def __init__(self, system):
        self._system = system
        self.all_alerts = {} # alert id -> alert
        self.active_alerts = {}  # alert id -> alert
        self.open_alerts = {}  # alert id -> alert

    def serialize(self, write):
        write(b'Alerts\n')
        write(b'/Alerts\n')

    def deserialize(self, read):
        if read() != b'Alerts\n':
            raise ModelDeserializeError()
        if read() != b'/Alerts\n':
            raise ModelDeserializeError()

    def get_all_alerts(self):
        return list(self.all_alerts.values())

    def get_active_alerts(self):
        return list(self.active_alerts.values())

    def get_open_alerts(self):
        return list(self.open_alerts.values())

    def get_closed_alerts(self):
        return [a for a in self.all_alerts.values() if a.alert_id not in self.open_alerts]

    def get_stream_active_alerts(self, stream_id):
        return [a for a in self.active_alerts.values() if a.stream_id == stream_id]

    def get_stream_open_alerts(self, stream_id):
        return [a for a in self.open_alerts.values() if a.stream_id == stream_id]

    def create_alert(self, alert_type, severity, stream_id, stream_label, path):
        alert = Alert(
            system=self._system,
            alert_type=alert_type,
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
        _update_view(alert, self.active_alerts, alert.is_active())
        _update_view(alert, self.open_alerts, alert.is_open())


def _update_view(alert, view, present):
    if present:
        view[alert.id] = alert
    else:
        view.pop(alert.id)
