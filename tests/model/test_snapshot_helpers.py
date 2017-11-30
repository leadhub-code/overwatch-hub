import yaml

from overwatch_hub.model.snapshot_helpers import snapshot_to_items
from overwatch_hub.model.snapshot_helpers import insert_point_to_history_items
from overwatch_hub.model.snapshot_helpers import retrieve_point_from_history_items

from overwatch_hub.util.datetime import parse_date_to_timestamp_ms


sample_snapshot = yaml.load('''
    address: https://www.messa.cz/cs/
    response:
      content_length: 1234
      duration: 0.12
      status_code:
        __check: {state: green}
        __value: 200
    watchdog:
      __watchdog: {deadline: 123900}
''')

sample_snapshot_2 = yaml.load('''
    address: https://www.messa.cz/cs/
    response:
      content_length: 1234
      duration: 0.44
      status_code:
        __check: {state: green}
        __value: 200
    watchdog:
      __watchdog: {deadline: 124900}
''')


def test_snapshot_to_items():
    assert snapshot_to_items(sample_snapshot) == {
        ('address',): {
            'value': 'https://www.messa.cz/cs/'},
        ('response', 'status_code'): {
            'value': 200,
            'check': {'state': 'green'}},
        ('response', 'content_length'): {
            'value': 1234},
        ('response', 'duration'): {
            'value': 0.12},
        ('watchdog',): {
            'watchdog': {'deadline': 123900},
        },
    }


def test_history_items():
    snapshot_items = {
        ('address',): {'value': 'https://www.messa.cz/cs/'},
        ('response', 'status_code'): {'check': {'state': 'green'}, 'value': 200},
        ('response', 'content_length'): {'value': 1234},
        ('response', 'duration'): {'value': 0.12},
        ('watchdog',): {'watchdog': {'deadline': 123900}},
    }
    history_items = {}
    date = parse_date_to_timestamp_ms('2017-11-22T10:20:30.123456')
    assert isinstance(date, int)
    insert_point_to_history_items(history_items, date, snapshot_items)
    assert history_items == {
        ('address',): {'value_history': {date: 'https://www.messa.cz/cs/'}},
        ('response', 'status_code'): {
            'check_history': {date: {'state': 'green'}},
            'value_history': {date: 200}
        },
        ('response', 'content_length'): {'value_history': {date: 1234}},
        ('response', 'duration'): {'value_history': {date: 0.12}},
        ('watchdog',): {'watchdog_history': {date: {'deadline': 123900}}},
    }
    s2 = retrieve_point_from_history_items(history_items, date)
    assert s2 == snapshot_items
