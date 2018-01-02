from pytest import skip
import yaml

from overwatch_hub.model import Model

from overwatch_hub.util.datetime import parse_date_to_timestamp_ms


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
