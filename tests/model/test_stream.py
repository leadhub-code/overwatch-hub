import yaml

from overwatch_hub.model.stream import flatten_snapshot


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


def test_flatten_snapshot():
    assert flatten_snapshot(sample_snapshot) == {
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
1
