import logging

from .alert import Alert
from .errors import ModelDeserializeError


logger = logging.getLogger(__name__)


class Alerts:

    _Alert = Alert

    def __init__(self, system):
        self._system = system
        self._all_alerts = {} # alert id -> alert
        self._active_alerts = {}  # alert id -> alert
        self._open_alerts = {}  # alert id -> alert

    def serialize(self, write):
        write(b'Alerts\n')
        for alert_id, alert in sorted(self._all_alerts.items()):
            write(b'-alert\n')
            alert.serialize(write)
        write(b'/Alerts\n')

    def deserialize(self, readline):
        if readline() != b'Alerts\n':
            raise ModelDeserializeError()
        while True:
            line = readline()
            if line == b'/Alerts\n':
                break
            elif line == b'-alert\n':
                alert = self._Alert.revive(
                    readline,
                    system=self._system,
                    update_callback=self._alert_updated)
                self._all_alerts[alert.id] = alert
                self._update_views(alert)
            else:
                raise ModelDeserializeError()

    def get_all_alerts(self):
        return list(self._all_alerts.values())

    def get_active_alerts(self):
        return list(self._active_alerts.values())

    def get_open_alerts(self):
        return list(self._open_alerts.values())

    def get_closed_alerts(self):
        return [a for a in self._all_alerts.values() if a.alert_id not in self._open_alerts]

    def get_stream_active_alerts(self, stream_id):
        return [a for a in self._active_alerts.values() if a.stream_id == stream_id]

    def get_stream_open_alerts(self, stream_id):
        return [a for a in self._open_alerts.values() if a.stream_id == stream_id]

    def create_alert(self, alert_type, severity, stream_id, stream_label, path):
        alert = self._Alert.create(
            alert_type=alert_type,
            severity=severity,
            stream_id=stream_id,
            stream_label=stream_label,
            path=path,
            system=self._system,
            update_callback=self._alert_updated)
        if alert.id in self._all_alerts:
            raise Exception('non-unique alert id')
        self._all_alerts[alert.id] = alert
        self._update_views(alert)

    def _alert_updated(self, alert):
        '''
        Passed as callback to Alert objects so this method is called whenever
        Alert changes its attributes.
        '''
        assert alert.id in self._all_alerts
        self._update_views(alert)

    def _update_views(self, alert):
        assert alert.id in self._all_alerts
        _update_view(alert, self._active_alerts, alert.is_active())
        _update_view(alert, self._open_alerts, alert.is_open())


def _update_view(alert, view, present):
    if present:
        view[alert.id] = alert
    else:
        view.pop(alert.id)
