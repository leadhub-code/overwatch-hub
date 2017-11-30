import logging
import yaml

from overwatch_hub.model import Model

from overwatch_hub.util.datetime import parse_date_to_timestamp_ms


logger = logging.getLogger(__name__)


sample_datapoints = yaml.load('''
    - date: 1511527495508
      label:
        agent: web_check
        host: wch1.example.com
      snapshot:
        by_endpoint:
          homepage_cs:
            url: https://example.com/cs/
            duration: 0.999
          homepage_en:
            url: https://example.com/en/
            duration: 0.175

    - date: 1511527802038
      label:
        agent: web_check
        host: wch1.example.com
      snapshot:
        by_endpoint:
          homepage_cs:
            url: https://example.com/cs/
            duration: 0.125
          homepage_en:
            url: https://example.com/en/
            duration: 0.111

    - date: 1511527726026
      label:
        agent: web_check
        host: wch2.example.com
      snapshot:
        by_endpoint:
          homepage_cs:
            url: https://example.com/cs/
            duration: 0.160
          homepage_en:
            url: https://example.com/en/
            duration: 0.190

    - date: 1511527495508
      label:
        agent: other_check
        host: wch1.example.com
      snapshot:
        by_endpoint:
          something_else:
            duration: 0.999
''')


def test_custom_check_with_no_alert():
    sample_datapoint = yaml.load('''
        date: 1511527495508
        label:
            agent: web_check
            host: wch1.example.com
        snapshot:
            by_endpoint:
                homepage_cs:
                    url: https://example.com/cs/
                    duration: 0.180
    ''')
    m = Model()
    ch = m.custom_checks.add_custom_check(
        label_filter={'agent': 'web_check'},
        path_filter=('by_endpoint', '*', 'duration'),
        red_value_filter={'$gte': 0.5})
    m.add_datapoint(**sample_datapoint)
    assert ch.get_current_alerts() == []
    assert ch.get_all_alerts() == []


def test_custom_check_with_alert():
    sample_datapoint = yaml.load('''
        date: 1511527495508
        label:
            agent: web_check
            host: wch1.example.com
        snapshot:
            by_endpoint:
                homepage_cs:
                    url: https://example.com/cs/
                    duration: 0.978
    ''')
    m = Model()
    ch = m.add_custom_check(
        label_filter={'agent': 'web_check'},
        path_filter=('by_endpoint', '*', 'duration'),
        red_value_filter={'$gte': 0.5})
    m.add_datapoint(**sample_datapoint)
    alert, = ch.get_current_alerts()
    assert alert == {
        'id': alert['id'],
        'stream_id': alert['stream_id'],
        'stream_label': {'agent': 'web_check', 'host': 'wch1.example.com'},
        'path': ('by_endpoint', 'homepage_cs', 'duration'),
        'initial_value': 0.978,
        'current_value': 0.978,
        'start_date': 1511527495508,
        'end_date': None,
    }
    assert ch.get_all_alerts() == [alert]


def test_custom_check_added_after_datapoint():
    sample_datapoint = yaml.load('''
        date: 1511527495508
        label:
            agent: web_check
            host: wch1.example.com
        snapshot:
            by_endpoint:
                homepage_cs:
                    url: https://example.com/cs/
                    duration: 0.978
    ''')
    m = Model()
    m.add_datapoint(**sample_datapoint)
    ch = m.add_custom_check(
        label_filter={'agent': 'web_check'},
        path_filter=('by_endpoint', '*', 'duration'),
        red_value_filter={'$gte': 0.5})
    alert, = ch.get_current_alerts()
    assert alert == {
        'id': alert['id'],
        'stream_id': alert['stream_id'],
        'stream_label': {'agent': 'web_check', 'host': 'wch1.example.com'},
        'path': ('by_endpoint', 'homepage_cs', 'duration'),
        'initial_value': 0.978,
        'current_value': 0.978,
        'start_date': 1511527495508,
        'end_date': None,
    }
    assert ch.get_all_alerts() == [alert]


def test_custom_check_with_multiple_alerts():
    sample_datapoints = yaml.load('''
      - date: 1511527495508
        label:
            agent: web_check
            host: wch1.example.com
        snapshot:
            by_endpoint:
                homepage_cs:
                    url: https://example.com/cs/
                    duration: 0.978
                homepage_en:
                    url: https://example.com/en/
                    duration: 0.175
      - date: 1511527495678
        label:
            agent: web_check
            host: wch2.example.com
        snapshot:
            by_endpoint:
                homepage_cs:
                    url: https://example.com/cs/
                    duration: 0.810
                homepage_en:
                    url: https://example.com/en/
                    duration: 0.820
    ''')
    m = Model()
    ch = m.custom_checks.add_custom_check(
        label_filter={'agent': 'web_check'},
        path_filter=('by_endpoint', '*', 'duration'),
        red_value_filter={'$gte': 0.5})
    for dp in sample_datapoints:
        m.add_datapoint(**dp)
    alerts = ch.get_current_alerts()
    assert ch.get_all_alerts() == alerts
    assert len(alerts) == 3
    alerts.sort(key=lambda alert: (alert['start_date'], alert['path']))
    assert alerts == [
        {
            'id': alerts[0]['id'],
            'stream_id': alerts[0]['stream_id'],
            'stream_label': {'agent': 'web_check', 'host': 'wch1.example.com'},
            'path': ('by_endpoint', 'homepage_cs', 'duration'),
            'initial_value': 0.978,
            'current_value': 0.978,
            'start_date': 1511527495508,
            'end_date': None
        }, {
            'id': alerts[1]['id'],
            'stream_id': alerts[1]['stream_id'],
            'stream_label': {'agent': 'web_check', 'host': 'wch2.example.com'},
            'path': ('by_endpoint', 'homepage_cs', 'duration'),
            'initial_value': 0.81,
            'current_value': 0.81,
            'start_date': 1511527495678,
            'end_date': None
        }, {
            'id': alerts[2]['id'],
            'stream_id': alerts[2]['stream_id'],
            'stream_label': {'agent': 'web_check', 'host': 'wch2.example.com'},
            'path': ('by_endpoint', 'homepage_en', 'duration'),
            'initial_value': 0.82,
            'current_value': 0.82,
            'start_date': 1511527495678,
            'end_date': None
        }]
