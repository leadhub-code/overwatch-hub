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


def test_serialize_empty_model():
    m = Model()
    data = m.serialize()
    assert data == b'Model\n-streams\nStreams\n/Streams\n-alerts\nAlerts\n/Alerts\n/Model\n'
    assert Model.revive(data)


def test_serialize_empty_model_with_custom_read_write_functions():
    m = Model()
    data = _serialize(m)
    assert data == [
        b'Model',
        b'-streams',
        b'Streams',
        b'/Streams',
        b'-alerts',
        b'Alerts',
        b'/Alerts',
        b'/Model',
    ]
    assert Model.revive(_it(data))
    m2 = Model()
    m2.deserialize(_it(data))


def test_serialize_model_with_datapoint():
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
    data = m.serialize()
    assert data.decode() == dedent('''\
        Model
        -streams
        Streams
        -stream
        Stream
        {"id":"S9CH0K8lHUiARv56","label":{"k1":"v1","k2":"v2"},"snapshot_dates":[1511346030123]}
        -item
        {"path": ["foo"]}
        StreamItem
        {"check_history":[],"current_check":null,"current_value":"bar","current_watchdog":null,"value_history":[[1511346030123,"bar"]],"watchdog_history":[]}
        /StreamItem
        -item
        {"path": ["response"]}
        StreamItem
        {"check_history":[[1511346030123,{"state":"green"}]],"current_check":{"state":"green"},"current_value":200,"current_watchdog":null,"value_history":[[1511346030123,200]],"watchdog_history":[]}
        /StreamItem
        -item
        {"path": ["watchdog"]}
        StreamItem
        {"check_history":[],"current_check":null,"current_value":null,"current_watchdog":{"deadline":1511346090000},"value_history":[],"watchdog_history":[[1511346030123,{"deadline":1511346090000}]]}
        /StreamItem
        /Stream
        /Streams
        -alerts
        Alerts
        /Alerts
        /Model
    ''')
    m2 = Model.revive(data)
    data2 = m2.serialize()
    assert data2 == data
