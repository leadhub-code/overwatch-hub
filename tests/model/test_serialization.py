from pytest import skip
import yaml

from overwatch_hub.model import Model


def serialize(obj):
    data = []
    obj.serialize(data.append)
    return data


def it(lst):
    iterator = iter(lst)
    return lambda: next(iterator)


def test_serialize_empty_model():
    m = Model()
    data = m.serialize()
    assert data == b'Model\n/Model\n'
    assert Model.revive(data)


def test_serialize_empty_model_with_custom_read_write_functions():
    m = Model()
    data = serialize(m)
    assert data == [
        b'Model',
        b'/Model',
    ]
    assert Model.revive(it(data))


def test_serialize_model_with_datapoint():
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
                   state: green
           watchdog:
               __watchdog:
                   deadline: 1511346090000
   ''')
    m = Model()
    m.add_datapoint(**sample_datapoint)
    assert serialize(m) == []
