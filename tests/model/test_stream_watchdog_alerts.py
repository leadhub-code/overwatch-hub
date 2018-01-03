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
                    'deadline': (deterministic_time.time() - 10) * 1000,
                },
            },
        })
    alert, = m.alerts.get_active_alerts()
    assert alert.alert_type == 'watchdog'
    assert alert.is_active == True
    assert alert.severity == 'red'
    assert alert.stream_label == {'k1': 'v1', 'k2': 'v2'}
    assert alert.path == ('watchdog',)


def test_watchdog_alert_is_created_only_once(system, deterministic_time):
    m = Model(system=system)
    for i in range(3):
        m.streams.add_datapoint(
            timestamp_ms=deterministic_time.time() * 1000,
            label={'k1': 'v1', 'k2': 'v2'},
            snapshot={
                'watchdog': {
                    '__watchdog': {
                        'deadline': (deterministic_time.time() - 3600) * 1000,
                    },
                },
            })
        deterministic_time.advance(seconds=30)
    assert len(m.alerts.get_active_alerts()) == 1
    assert len(m.alerts.get_all_alerts()) == 1


def test_watchdog_alert_gets_deactivated_when_watchdog_becomes_ok(system, deterministic_time):
    m = Model(system=system)
    m.streams.add_datapoint(
        timestamp_ms=deterministic_time.time() * 1000,
        label={'k1': 'v1', 'k2': 'v2'},
        snapshot={
            'watchdog': {
                '__watchdog': {
                    'deadline': (deterministic_time.time() - 10) * 1000,
                },
            },
        })
    alert, = m.alerts.get_active_alerts()
    assert alert.is_active == True
    deterministic_time.advance(seconds=30)
    m.streams.add_datapoint(
        timestamp_ms=deterministic_time.time() * 1000,
        label={'k1': 'v1', 'k2': 'v2'},
        snapshot={
            'watchdog': {
                '__watchdog': {
                    'deadline': (deterministic_time.time() + 10) * 1000,
                },
            },
        })
    assert alert.is_active == False
    assert m.alerts.get_active_alerts() == []
