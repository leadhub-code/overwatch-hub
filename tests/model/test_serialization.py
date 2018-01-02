import io
from pytest import skip
from textwrap import dedent
import yaml

from overwatch_hub.model import Model


def _serialize(obj):
    data = []
    obj.serialize(data.append)
    return data


def _it(lst):
    iterator = iter(lst)
    return lambda: next(iterator)


def test_serialize_and_revive_empty_model():
    m = Model()
    data = m.serialize()
    expected = dedent('''\
        Model
        -streams
        Streams
        /Streams
        -alerts
        Alerts
        /Alerts
        /Model
    ''').encode()
    assert data == expected
    buf = []
    m.serialize(buf.append)
    assert b''.join(buf) == expected
    assert Model.revive(data)
    assert Model.revive(io.BytesIO(data))
    assert Model.revive(io.BytesIO(data).readline)


def test_serialize_and_revive_model_with_datapoint():
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
    data = m.serialize()
    expected = dedent('''\
        Model
        -streams
        Streams
        -stream
        Stream
        {"id":"S9CH0K8lHUiARv56","label":{"k1":"v1","k2":"v2"},"snapshot_dates":[1511346030123]}
        -item
        {"path":["foo"]}
        StreamItem
        {"check_history":[],"current_check":null,"current_value":"bar","current_watchdog":null,"value_history":[[1511346030123,"bar"]],"watchdog_history":[]}
        /StreamItem
        -item
        {"path":["response"]}
        StreamItem
        {"check_history":[[1511346030123,{"state":"green"}]],"current_check":{"state":"green"},"current_value":200,"current_watchdog":null,"value_history":[[1511346030123,200]],"watchdog_history":[]}
        /StreamItem
        -item
        {"path":["watchdog"]}
        StreamItem
        {"check_history":[],"current_check":null,"current_value":null,"current_watchdog":{"deadline":1511346090000},"value_history":[],"watchdog_history":[[1511346030123,{"deadline":1511346090000}]]}
        /StreamItem
        /Stream
        /Streams
        -alerts
        Alerts
        /Alerts
        /Model
    ''').encode()
    assert data == expected
    assert Model.revive(data).serialize() == data
