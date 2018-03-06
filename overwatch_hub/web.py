from aiohttp.web import json_response as aiohttp_json_response
from aiohttp.web import HTTPForbidden
import logging
import random
import simplejson as json
from time import time
import yaml

from .util.datetime import parse_date_to_timestamp_ms


logger = logging.getLogger(__name__)


def json_response(reply, status=200):
    return aiohttp_json_response(reply, dumps=json.dumps, status=status)


class Auth:

    def __init__(self, configuration):
        self.configuration = configuration

    def check_report_authorization(self, request):
        token = self._get_authorization_token(request)
        if token not in self.configuration.report_tokens:
            logger.info('Invalid Authorization token: %s...', repr(token[:5]))
            raise HTTPForbidden(reason='Invalid Authorization token')

    def check_client_authorization(self, request):
        token = self._get_authorization_token(request)
        if token not in self.configuration.client_tokens:
            logger.info('Invalid Authorization token: %s...', repr(token[:5]))
            raise HTTPForbidden(reason='Invalid Authorization token')

    def _get_authorization_token(self, request):
        auth_value = request.headers.get('Authorization')
        if not auth_value:
             raise HTTPForbidden(reason='Missing Authorization header')
        parts = auth_value.split()
        if len(parts) != 2:
            raise HTTPForbidden(reason='Unsupported Authorization header value format')
        _, token = parts
        return token


class Serialization:

    def __init__(self, model):
        self.model = model

    def dump_stream(self, stream):
        open_alerts = self.model.alerts.get_stream_open_alerts(stream_id=stream.id)
        open_check_alerts = [a for a in open_alerts if a.alert_type == 'check']
        open_watchdog_alerts = [a for a in open_alerts if a.alert_type == 'watchdog']
        return {
            'id': stream.id,
            'label': stream.label,
            'last_date': stream.get_last_date(),
            'check_count': len(stream.get_current_checks()),
            'watchdog_count': len(stream.get_current_watchdogs()),
            'check_alert_count': len(open_check_alerts),
            'watchdog_alert_count': len(open_watchdog_alerts),
        }

    def dump_snapshot_items(self, snapshot_items):
        return [{'path': path, **item} for path, item in snapshot_items.items()]


class Handlers:

    def __init__(self, configuration, model):
        self.configuration = configuration
        self.model = model
        self.auth = Auth(self.configuration)
        self.serialization = Serialization(model=self.model)

    def register(self, router):
        router.add_get('/', self.get_index)
        router.add_post('/report', self.post_report)
        router.add_get('/streams/', self.get_stream_list)
        router.add_get('/streams/{stream_id}', self.get_stream_detail)
        router.add_get('/alerts/current', self.get_current_alert_list)
        router.add_get('/alerts/closed', self.get_closed_alert_list)

    async def get_index(self, request):
        return json_response({'info': 'Overwatch Hub'})

    async def post_report(self, request):
        self.auth.check_report_authorization(request)
        body = await request.json()
        #logger.debug('body:\n%s', yaml.dump(body))
        now_ms = int(time() * 1000)
        if body.get('date'):
            timestamp_ms = int(parse_date_to_timestamp_ms(body['date']))
        else:
            timestamp_ms = now_ms
        if timestamp_ms > now_ms:
            logger.info('Datapoint timestamp %s > now %s', timestamp_ms, now_ms)
            timestamp_ms = now_ms
        state = body.get('state') or body.get('values')
        if not state or not isinstance(state, dict):
            raise Exception('Invalid state data')
        self.model.streams.add_datapoint(
            label=body['label'],
            timestamp_ms=timestamp_ms,
            snapshot=state)
        return json_response({'ok': True})

    async def get_stream_list(self, request):
        self.auth.check_client_authorization(request)
        self.model.check_watchdogs()
        return json_response({
            'streams': [self.serialization.dump_stream(s) for s in self.model.streams.get_all()],
        })

    async def get_stream_detail(self, request):
        self.auth.check_client_authorization(request)
        stream_id = request.match_info['stream_id']
        self.model.check_watchdogs()
        try:
            stream = self.model.streams.get_by_id(stream_id)
        except KeyError as e:
            logger.info('Got %r for streams.get_by_id(%r), returning 404', e, stream_id)
            return json_response({'error': {'code': 'stream_not_found'}}, status=404)
        current_date, current_items = stream.get_current_datapoint()
        #current_alerts = stream.get_current_check_alerts() + stream.get_current_watchdog_alerts()
        reply = {
            'stream': self.serialization.dump_stream(stream),
            'current_datapoint': {
                'date': current_date,
                'items': self.serialization.dump_snapshot_items(current_items),
            },
            #'current_alerts': current_alerts,
            #'history_items': self._dump_snapshot_items(stream.history_items),
        }
        return json_response(reply)

    async def get_current_alert_list(self, request):
        self.auth.check_client_authorization(request)
        self.model.check_watchdogs()
        alerts = self.model.alerts.get_open_alerts()
        assert all(not a.end_date for a in alerts)
        alerts.sort(key=lambda a: a['start_date'], reverse=True)
        return json_response({'alerts': alerts[:1000]})

    async def get_closed_alert_list(self, request):
        self.auth.check_client_authorization(request)
        self.model.check_watchdogs()
        alerts = self.model.alerts.get_closed_alerts()
        alerts = [a for a in alerts if a['end_date']]
        alerts.sort(key=lambda a: a['start_date'], reverse=True)
        return json_response({'alerts': alerts[:1000]})
