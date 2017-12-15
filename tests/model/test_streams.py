from pytest import skip
import yaml

from overwatch_hub.model import Model

from overwatch_hub.util.datetime import parse_date_to_timestamp_ms


def test_add_datapoint_and_check_stream_attributes():
    sample_datapoint = yaml.load('''
        timestamp_ms: 1511346030123
        label:
            k1: v1
            k2: v2
        snapshot:
            foo: bar
            response:
                __value: 200
                __check:
                    state: green
            watchdog:
                __watchdog:
                    deadline: 1511346090000
    ''')
    m = Model()
    m.streams.add_datapoint(**sample_datapoint)
    stream, = m.streams.get_all()
    assert stream.id
    assert stream.label == {'k1': 'v1', 'k2': 'v2'}
    data = m.serialize()
    assert Model.revive(data).serialize() == data

    """
    assert stream.dates == {1511346030123}
    assert stream.history_items == {
        ('foo',): {
            'value_history': {1511346030123: 'bar'},
        },
        ('response',): {
            'check_history': {1511346030123: {'state': 'green'}},
            'value_history': {1511346030123: 200}},
        ('watchdog',): {
            'watchdog_history': {1511346030123: {'deadline': 1511346090000}},
        },
    }
    assert stream.get_current_datapoint() == (
        1511346030123, {
            ('foo',): {'value': 'bar'},
            ('response',): {'check': {'state': 'green'}, 'value': 200},
            ('watchdog',): {'watchdog': {'deadline': 1511346090000}},
        })
    assert stream.get_current_checks() == (
        1511346030123, {('response',): {'state': 'green'}})
    assert stream.get_current_watchdogs() == (
        1511346030123, {('watchdog',): {'deadline': 1511346090000}})
    """


def test_stream_creates_alert_for_red_check():
    skip()
    sample_datapoint = yaml.load('''
        date: 1511346030123
        label:
            k1: v1
            k2: v2
        snapshot:
            foo: bar
            response:
                __value: 200
                __check:
                    state: red
    ''')
    m = Model()
    m.add_datapoint(**sample_datapoint)
    stream, = m.streams.get_all()
    assert stream.get_current_checks() == (
        1511346030123, {('response',): {'state': 'red'}})
    alert, = stream.get_current_check_alerts()
    assert alert == {
        'type': 'check_alert',
        'id': alert['id'],
        'stream_label': {'k1': 'v1', 'k2': 'v2'},
        'path': ('response',),
        'initial_state': 'red',
        'current_state': 'red',
        'start_date': 1511346030123,
        'end_date': None,
    }


def test_stream_resolves_check_alert():
    skip()
    sample_datapoint = yaml.load('''
        date: 1511346030123
        label:
            k1: v1
            k2: v2
        snapshot:
            foo: bar
            response:
                __value: 200
                __check:
                    state: red
    ''')
    m = Model()
    m.add_datapoint(**sample_datapoint)
    stream, = m.streams.get_all()
    assert len(stream.get_current_check_alerts()) == 1
    sample_datapoint['date'] += 5000
    sample_datapoint['snapshot']['response']['__check']['state'] = 'green'
    m.add_datapoint(**sample_datapoint)
    assert stream.get_current_check_alerts() == []
    alert, = stream.get_all_check_alerts()
    assert alert['end_date'] == 1511346030123 + 5000


def test_stream_creates_alert_for_expired_watchdog():
    skip()
    sample_datapoint = yaml.load('''
        date: 1511346030123
        label:
            k1: v1
            k2: v2
        snapshot:
            foo: bar
            watchdog:
                __watchdog:
                    deadline: 1511346039000
    ''')
    m = Model()
    m.add_datapoint(**sample_datapoint)
    stream, = m.streams.get_all()
    assert stream.get_current_watchdogs() == (
        1511346030123, {('watchdog',): {'deadline': 1511346039000}})
    assert stream.get_current_watchdog_alerts() == []
    m.check_watchdogs(1511346038000)
    assert stream.get_current_watchdog_alerts() == []
    m.check_watchdogs(1511346039500)
    alert, = stream.get_current_watchdog_alerts()
    assert alert == {
        'deadline': 1511346039000,
        'end_date': None,
        'id': alert['id'],
        'path': ('watchdog',),
        'start_date': 1511346039500,
        'stream_label': {'k1': 'v1', 'k2': 'v2'},
        'type': 'watchdog_alert',
    }
    assert stream.get_all_watchdog_alerts() == [alert]


def test_stream_resolves_watchdog_alert():
    skip()
    sample_datapoint = yaml.load('''
        date: 1511346030123
        label:
            k1: v1
            k2: v2
        snapshot:
            foo: bar
            watchdog:
                __watchdog:
                    deadline: 1511346039000
    ''')
    m = Model()
    m.add_datapoint(**sample_datapoint)
    stream, = m.streams.get_all()
    m.check_watchdogs(1511346039500)
    assert len(stream.get_current_watchdog_alerts()) == 1
    sample_datapoint['date'] = 1511346040000
    sample_datapoint['snapshot']['watchdog']['__watchdog']['deadline'] = 1511346090000
    m.add_datapoint(**sample_datapoint)
    m.check_watchdogs(1511346050000)
    assert stream.get_current_watchdog_alerts() == []
    alert, = stream.get_all_watchdog_alerts()
