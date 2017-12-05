import logging
from time import time
from uuid import uuid4

from ..util import intern_keys

from .snapshot_helpers import snapshot_to_items
from .snapshot_helpers import insert_point_to_history_items
from .snapshot_helpers import retrieve_point_from_history_items


logger = logging.getLogger(__name__)


class Stream:

    def __init__(self, label):
        assert isinstance(label, dict)
        self.id = uuid4().hex
        self.label = label
        self.dates = set()
        self.last_date = None
        self.history_items = {} # {path: {value_history, check_history}}
        self.current_check_alerts_by_path = {}
        self.check_alerts_by_id = {}
        self.current_watchdog_alerts_by_path = {}
        self.watchdog_alerts_by_id = {}

    def serialize(self):
        return {
            'id': self.id,
            'label': self.label,
            'dates': list(self.dates),
            'history_items': list(self.history_items.items()),
            'check_alerts': list(self.check_alerts_by_id.values()),
            'watchdog_alerts': list(self.watchdog_alerts_by_id.values()),
        }

    @classmethod
    def deserialize(cls, data):
        stream = cls(label=data['label'])
        stream.id = data['id']
        stream.dates = set(data['dates'])
        stream.last_date = max(stream.dates)
        stream.history_items = dict(data['history_items'])
        for a in data['check_alerts']:
            stream.check_alerts_by_id[a['id']] = a
            if not a['end_date']:
                stream.current_check_alerts_by_path[a['path']] = a
        for a in data['watchdog_alerts']:
            stream.watchdog_alerts_by_id[a['id']] = a
            if not a['end_date']:
                stream.current_watchdog_alerts_by_path[a['path']] = a
        return stream

    def add_datapoint(self, timestamp_ms, snapshot):
        snapshot_items = snapshot_to_items(snapshot)
        insert_point_to_history_items(self.history_items, timestamp_ms, snapshot_items)
        self.dates.add(timestamp_ms)
        if self.last_date is None or timestamp_ms >= self.last_date:
            self.last_date = timestamp_ms
            self._process_checks()

    def check_watchdogs(self, now_date):
        self._process_watchdogs(now_date)

    def get_current_datapoint(self):
        '''
        Returns (timestamp in ms, snapshot items)
        '''
        current_items = retrieve_point_from_history_items(self.history_items, self.last_date)
        return self.last_date, current_items

    def get_current_checks(self):
        current_date, current_items = self.get_current_datapoint()
        checks = {}
        for path, item in current_items.items():
            if item.get('check'):
                checks[path] = {
                    'state': item['check']['state'],
                }
        return current_date, checks

    def get_current_watchdogs(self):
        current_date, current_items = self.get_current_datapoint()
        checks = {}
        for path, item in current_items.items():
            if item.get('watchdog'):
                checks[path] = {
                    'deadline': item['watchdog']['deadline'],
                }
        return current_date, checks

    def _process_checks(self):
        current_date, current_checks = self.get_current_checks()
        alert_paths = set()
        for path, check in current_checks.items():
            assert isinstance(path, tuple)
            if check['state'] != 'green':
                alert_paths.add(path)
                self._ensure_check_alert(current_date, path, check)
        for path, alert in list(self.current_check_alerts_by_path.items()):
            if path not in alert_paths:
                alert['end_date'] = current_date
                self.current_check_alerts_by_path.pop(path)

    def _process_watchdogs(self, now_date):
        current_date, current_watchdogs = self.get_current_watchdogs()
        alert_paths = set()
        for path, watchdog in current_watchdogs.items():
            assert isinstance(path, tuple)
            if watchdog['deadline'] <= now_date:
                alert_paths.add(path)
                self._ensure_watchdog_alert(now_date, path, watchdog)
        for path, alert in list(self.current_watchdog_alerts_by_path.items()):
            if path not in alert_paths:
                alert['end_date'] = now_date
                self.current_watchdog_alerts_by_path.pop(path)

    def _ensure_check_alert(self, current_date, path, check):
        alert = self.current_check_alerts_by_path.get(path)
        if alert is None:
            alert = {
                'type': 'check_alert',
                'id': uuid4().hex,
                'stream_label': self.label,
                'path': path,
                'initial_state': check['state'],
                'current_state': check['state'],
                'start_date': current_date,
                'end_date': None,
            }
            alert = intern_keys(alert)
            self.current_check_alerts_by_path[path] = alert
            self.check_alerts_by_id[alert['id']] = alert
            logger.info('Created new stream check alert: %s', alert)
        alert['current_state'] = check['state']
        return alert

    def _ensure_watchdog_alert(self, now_date, path, watchdog):
        alert = self.current_watchdog_alerts_by_path.get(path)
        if alert is None:
            alert = {
                'type': 'watchdog_alert',
                'id': uuid4().hex,
                'stream_label': self.label,
                'path': path,
                'deadline': watchdog['deadline'],
                'start_date': now_date,
                'end_date': None,
            }
            alert = intern_keys(alert)
            self.current_watchdog_alerts_by_path[path] = alert
            self.watchdog_alerts_by_id[alert['id']] = alert
            logger.info('Created new stream watchdog alert: %s', alert)
        return alert

    def get_current_check_alerts(self):
        return list(self.current_check_alerts_by_path.values())

    def get_all_check_alerts(self):
        return list(self.check_alerts_by_id.values())

    def get_current_watchdog_alerts(self):
        return list(self.current_watchdog_alerts_by_path.values())

    def get_all_watchdog_alerts(self):
        return list(self.watchdog_alerts_by_id.values())
