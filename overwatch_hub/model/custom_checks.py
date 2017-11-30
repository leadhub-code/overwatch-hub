import logging
from time import time
from uuid import uuid4


logger = logging.getLogger(__name__)


class CustomChecks:

    def __init__(self):
        self._by_id = {}

    def add_custom_check(self, label_filter, path_filter, red_value_filter):
        ch = CustomCheck(label_filter, path_filter, red_value_filter)
        self._by_id[ch.id] = ch
        logger.info('Added custom check %s label: %s path: %s', ch.id, ch.label_filter, ch.path_filter)
        return ch

    def get_all(self):
        return list(self._by_id.values())

    def check_stream(self, stream):
        for ch in self._by_id.values():
            ch.check_stream(stream)

    def serialize(self):
        return [ch.serialize() for ch in self._by_id.values()]

    @classmethod
    def deserialize(cls, data):
        chs = cls()
        for ch_data in data:
            ch = CustomCheck.deserialize(ch_data)
            chs._by_id[ch.id] = ch
        return chs


class CustomCheck:

    def __init__(self, label_filter, path_filter, red_value_filter):
        assert isinstance(label_filter, dict)
        self.id = uuid4().hex
        self.created_timestamp_ms = int(time() * 1000)
        self.label_filter = label_filter
        self.path_filter = path_filter
        self.red_value_filter = red_value_filter
        self.current_alerts_by_sp = {} # (stream.id, path) => { id, ... }
        self.alerts_by_id = {}

    def serialize(self):
        return {
            'id': self.id,
            'created_timestamp_ms': self.created_timestamp_ms,
            'label_filter': self.label_filter,
            'path_filter': self.path_filter,
            'red_value_filter': self.red_value_filter,
            'alerts': list(self.alerts_by_id.values()),
        }

    @classmethod
    def deserialize(cls, data):
        ch = cls(
            label_filter=data['label_filter'],
            path_filter=data['path_filter'],
            red_value_filter=data['red_value_filter'])
        ch.id = data['id']
        ch.created_timestamp_ms = data['created_timestamp_ms']
        for alert in data['alerts']:
            self.alerts_by_id[alert['id']] = alert
            if not a['end_date']:
                sp = (alert['stream_id'], alert['path'])
                self.current_alerts_by_sp[sp] = alert
        return ch

    def get_current_alerts(self):
        return list(self.current_alerts_by_sp.values())

    def get_all_alerts(self):
        return list(self.alerts_by_id.values())

    def check_stream(self, stream):
        if label_match(self.label_filter, stream.label):
            processed_alert_ids = set()
            current_date, current_items = stream.get_current_datapoint()
            for path, item in current_items.items():
                if 'value' in item and path_match(self.path_filter, path):
                    if value_match(self.red_value_filter, item['value']):
                        alert = self._ensure_value_alert(
                            stream, current_date, path, item['value'])
                        processed_alert_ids.add(alert['id'])
                    else:
                        alert = self.current_alerts_by_sp.get((stream.id, path))
                        if alert:
                            logger.info('Custom check alert resolved: %s', alert)
                            alert['end_date'] = current_date
                            self.current_alerts_by_sp.pop((stream.id, path))
                            processed_alert_ids.add(alert['id'])
            for sp, alert in list(self.current_alerts_by_sp.items()):
                if alert['stream_label'] == stream.label:
                    if alert['id'] not in processed_alert_ids:
                        logger.debug('Custom check alert %s not processed', alert)
            #         if alert['id'] not in current_alert_ids:
            #             alert['end_date'] = current_date
            #             self.current_alerts_by_sp.pop(sp)

    def _ensure_value_alert(self, stream, current_date, path, value):
        sp = (stream.id, path)
        alert = self.current_alerts_by_sp.get(sp)
        if alert is None:
            alert = {
                'id': uuid4().hex,
                'stream_id': stream.id,
                'stream_label': stream.label,
                'path': path,
                'initial_value': value,
                'current_value': value,
                'start_date': current_date,
                'end_date': None,
            }
            self.current_alerts_by_sp[sp] = alert
            self.alerts_by_id[alert['id']] = alert
            logger.info('Created new custom check alert: %s', alert)
        alert['current_value'] = value
        return alert


def label_match(label_filter, label):
    return all(label.get(k) == v for k, v in label_filter.items())


def path_match(path_filter, path):
    if len(path_filter) != len(path):
        return False
    for fk, pk in zip(path_filter, path):
        if fk != '*' and fk != pk:
            return False
    return True


def value_match(value_filter, value):
    if isinstance(value_filter, dict):
        for fk, fv in value_filter.items():
            if fk == '$gte':
                try:
                    if float(value) < float(fv):
                        return False
                except ValueError:
                    if str(value) < str(fv):
                        return False
            else:
                raise Exception('Unknown value_filter key: {!r}'.format(fk))
        return True
    else:
        raise Exception('Unsupported value_filter type: {!r}'.format(value_filter))


assert path_match(('a', 'b'), ('a', 'b'))
assert path_match(('a', '*'), ('a', 'b'))
assert path_match(('*', 'b'), ('a', 'b'))
assert not path_match(('a',), ('a', 'b'))
assert not path_match(('a', 'b', 'c'), ('a', 'b'))
assert not path_match(('*',), ('a', 'b'))
assert not path_match(('x', '*',), ('a', 'b'))
assert not path_match(('*', 'x',), ('a', 'b'))
