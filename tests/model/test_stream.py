from pytest import skip
import yaml

from overwatch_hub.model import Model


def _stable_serialization(model):
    data = model.serialize()
    return Model.revive(data).serialize() == data


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
    assert _stable_serialization(m)
    assert stream.items[('foo',)].current_value == 'bar'
    assert stream.items[('foo',)].value_history == {1511346030123: 'bar'}
    assert stream.items[('response',)].current_value == 200
    assert stream.items[('response',)].value_history == {1511346030123: 200}
    assert stream.items[('response',)].current_check == {'state': 'green'}
    assert stream.items[('response',)].check_history == {1511346030123: {'state': 'green'}}
    assert stream.items[('watchdog',)].current_watchdog == {'deadline': 1511346090000}
    assert stream.items[('watchdog',)].watchdog_history == {1511346030123: {'deadline': 1511346090000}}


def test_stream_creates_alert_for_red_check():
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
                    state: red
    ''')
    m = Model()
    m.streams.add_datapoint(**sample_datapoint)
    stream, = m.streams.get_all()
    assert stream.get_current_checks() == {('response',): {'state': 'red'}}
    skip()
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
