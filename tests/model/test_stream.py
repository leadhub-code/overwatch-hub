from pytest import skip
import yaml

from overwatch_hub.model import Model


def test_add_datapoint_and_check_stream_item_attributes():
    m = Model()
    m.streams.add_datapoint(
        timestamp_ms=1511346030123,
        label={'k1': 'v1', 'k2': 'v2'},
        snapshot=yaml.load('''
            foo: bar
            response:
                __value: 200
                __check:
                    state: green
            watchdog:
                __watchdog:
                    deadline: 1511346090000
        '''))
    stream, = m.streams.get_all()
    assert stream.id
    assert stream.label == {'k1': 'v1', 'k2': 'v2'}
    assert stream.snapshot_dates == [1511346030123]
    assert Model.revive(m.serialize()).serialize() == m.serialize()
    assert stream.items[('foo',)].current_value == 'bar'
    assert stream.items[('foo',)].value_history == {1511346030123: 'bar'}
    assert stream.items[('response',)].current_value == 200
    assert stream.items[('response',)].value_history == {1511346030123: 200}
    assert stream.items[('response',)].current_check == {'state': 'green'}
    assert stream.items[('response',)].check_history == {1511346030123: {'state': 'green'}}
    assert stream.items[('watchdog',)].current_watchdog == {'deadline': 1511346090000}
    assert stream.items[('watchdog',)].watchdog_history == {1511346030123: {'deadline': 1511346090000}}


def test_stream_creates_alert_for_red_check():
    m = Model()
    m.streams.add_datapoint(
        timestamp_ms=1511346030123,
        label={'k1': 'v1', 'k2': 'v2'},
        snapshot=yaml.load('''
            foo: bar
            response:
                __value: 500
                __check:
                    state: red
        '''))
    stream, = m.streams.get_all()
    assert stream.get_current_checks() == {('response',): {'state': 'red'}}
    alert, = m.alerts.get_active_alerts()
    assert alert.alert_type == 'check'
    assert alert.is_active == True
    assert alert.severity == 'red'
    assert alert.stream_label == {'k1': 'v1', 'k2': 'v2'}
    assert alert.path == ('response',)


def test_red_alert_gets_deactivated_when_check_returns_to_green():
    m = Model()
    m.streams.add_datapoint(
        timestamp_ms=1511346030123,
        label={'k1': 'v1', 'k2': 'v2'},
        snapshot=yaml.load('''
            foo: bar
            response:
                __value: 500
                __check:
                    state: red
        '''))
    stream, = m.streams.get_all()
    alert, = m.alerts.get_active_alerts()
    assert alert.is_active == True
    m.streams.add_datapoint(
        timestamp_ms=1511346035900,
        label={'k1': 'v1', 'k2': 'v2'},
        snapshot=yaml.load('''
            foo: bar
            response:
                __value: 200
                __check:
                    state: green
        '''))
    assert m.alerts.get_active_alerts() == []
    assert alert.is_active == False


def test_new_alert_is_created_when_check_transitions_from_red_to_yellow():
    m = Model()
    m.streams.add_datapoint(
        timestamp_ms=1511346030123,
        label={'k1': 'v1', 'k2': 'v2'},
        snapshot=yaml.load('''
            duration:
                __check:
                    state: red
        '''))
    stream, = m.streams.get_all()
    alert1, = m.alerts.get_active_alerts()
    assert alert1.is_active == True
    m.streams.add_datapoint(
        timestamp_ms=1511346035900,
        label={'k1': 'v1', 'k2': 'v2'},
        snapshot=yaml.load('''
            duration:
                __check:
                    state: yellow
        '''))
    alert2, = m.alerts.get_active_alerts()
    assert alert2.id != alert1.id
    assert alert1.severity == 'red'
    assert alert1.is_active == False
    assert alert2.severity == 'yellow'
    assert alert2.is_active == True


def test_new_alert_is_created_when_check_transitions_from_yellow_to_red():
    m = Model()
    m.streams.add_datapoint(
        timestamp_ms=1511346030123,
        label={'k1': 'v1', 'k2': 'v2'},
        snapshot=yaml.load('''
            duration:
                __check:
                    state: yellow
        '''))
    stream, = m.streams.get_all()
    alert1, = m.alerts.get_active_alerts()
    assert alert1.is_active == True
    m.streams.add_datapoint(
        timestamp_ms=1511346035900,
        label={'k1': 'v1', 'k2': 'v2'},
        snapshot=yaml.load('''
            duration:
                __check:
                    state: red
        '''))
    alert2, = m.alerts.get_active_alerts()
    assert alert2.id != alert1.id
    assert alert1.severity == 'yellow'
    assert alert1.is_active == False
    assert alert2.severity == 'red'
    assert alert2.is_active == True
