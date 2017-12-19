import logging
import simplejson as json
import sys
from sys import intern
from time import time
from uuid import uuid4

from ..util import intern_keys, serialize_label, sha256_b64, json_dumps_compact

from .errors import ModelDeserializeError
from .stream_item import StreamItem


logger = logging.getLogger(__name__)

py_dict_ordered = sys.version >= '3.6'


def generate_stream_id(label):
    r = serialize_label(label).encode()
    h = sha256_b64(r).replace('-', '').replace('_', '')
    return 'S' + h[:15]


assert generate_stream_id({'foo': 'bar'}) == 'STYFHh3z29EPT8mC'


def flatten_snapshot(snapshot):
    assert isinstance(snapshot, dict)
    s_check = intern('check')
    s_watchdog = intern('watchdog')
    s_value = intern('value')
    nodes_by_path = {}

    def get_node(path):
        assert isinstance(path, tuple)
        if path not in nodes_by_path:
            nodes_by_path[path] = {}
        return nodes_by_path[path]

    def r(path, obj):
        if isinstance(obj, dict):
            if obj.get('__check'):
                get_node(path)[s_check] = intern_keys(obj['__check'])

            if obj.get('__watchdog'):
                get_node(path)[s_watchdog] = intern_keys(obj['__watchdog'])

            if '__value' in obj:
                get_node(path)[s_value] = intern_keys(obj['__value'])

            for k, v in obj.items():
                if k.startswith('__'):
                    continue
                r(path + (intern(k), ), v)
        else:
            get_node(path)[s_value] = obj

    r(tuple(), snapshot)
    return nodes_by_path


assert flatten_snapshot({'foo': 'bar'}) == {('foo',): {'value': 'bar'}}


class Stream:

    def __init__(self, label):
        self.id = generate_stream_id(label)
        self.label = label
        self.snapshot_dates = []
        self.items = {} # path -> StreamItem

    def __repr__(self):
        return '<{cls} {s.id} {s.label!r}>'.format(
            cls=self.__class__.__name__,
            s=self)

    def serialize(self, write):
        write(b'Stream')
        data = {
            'id': self.id,
            'label': self.label,
            'snapshot_dates': self.snapshot_dates,
        }
        data_json = json_dumps_compact(data)
        assert json.loads(data_json) == data
        write(data_json.encode())
        for path, stream_item in sorted(self.items.items()):
            write(b'-item')
            write(json.dumps({'path': path}).encode())
            stream_item.serialize(write)
        write(b'/Stream')

    @classmethod
    def revive(cls, read):
        stream = cls(label={})
        stream.deserialize(read)
        return stream

    def deserialize(self, read):
        if read() != b'Stream':
            raise ModelDeserializeError()
        data = json.loads(read().decode())
        self.label = data['label']
        self.id = data['id']
        self.snapshot_dates = data['snapshot_dates']
        while True:
            x = read()
            if x == b'/Stream':
                break
            elif x == b'-item':
                item_data = json.loads(read().decode())
                item_path = tuple(item_data['path'])
                stream_item = StreamItem.revive(read)
                self.items[item_path] = stream_item
            else:
                raise ModelDeserializeError()

    def add_datapoint(self, timestamp_ms, snapshot):
        assert isinstance(timestamp_ms, int)
        snapshot_items = flatten_snapshot(snapshot)
        self.snapshot_dates.append(timestamp_ms)
        for path, item_data in snapshot_items.items():
            if path not in self.items:
                self.items[path] = StreamItem()
            stream_item = self.items[path]
            stream_item.add_snapshot(
                timestamp_ms,
                value=item_data.get('value'),
                check=item_data.get('check'),
                watchdog=item_data.get('watchdog'))
        for path, stream_item in self.items.items():
            if path not in snapshot_items:
                stream_item.add_snapshot(
                    timestamp_ms,
                    value=None,
                    check=None,
                    watchdog=None)
        '''
        insert_point_to_history_items(self.history_items, timestamp_ms, snapshot_items)
        self.dates.add(timestamp_ms)
        if self.last_date is None or timestamp_ms >= self.last_date:
            self.last_date = timestamp_ms
            self._process_checks()
        '''

"""
class OLDStream:

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
"""
