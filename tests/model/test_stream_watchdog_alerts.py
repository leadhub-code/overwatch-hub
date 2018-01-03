import yaml

from overwatch_hub.model import Model


def test_stream_creates_alert_for_expired_watchdog(system, deterministic_time):
    m = Model(system=system)
    m.streams.add_datapoint(
        timestamp_ms=1511346030123,
        label={'k1': 'v1', 'k2': 'v2'},
        snapshot={
            'watchdog': {
                '__watchdog': {
                    'deadline': (deterministic_time.time() - 10)  * 1000,
                },
            },
        })
    stream, = m.streams.get_all()
    assert stream.get_current_watchdogs() == {('watchdog',): {'deadline': 1515585590000}}
    alert, = m.alerts.get_active_alerts()
    '''
    assert alert.alert_type == 'check'
    assert alert.is_active == True
    assert alert.severity == 'red'
    assert alert.stream_label == {'k1': 'v1', 'k2': 'v2'}
    assert alert.path == ('response',)
    '''
