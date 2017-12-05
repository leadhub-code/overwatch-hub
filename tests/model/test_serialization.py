from pytest import skip
import yaml

from overwatch_hub.model import Model





def test_serialize_empty_model():
    m = Model()


def test_serialize_model_with_datapoint():
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
