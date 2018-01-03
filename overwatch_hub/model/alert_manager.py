import logging


logger = logging.getLogger(__name__)


class AlertManager:

    def __init__(self, alerts, system):
        self._alerts = alerts
        self._system = system

    def stream_updated(self, params):
        '''
        Handler pro event streams.on_stream_updated
        '''
        self.check_stream(params['stream'])

    def check_stream(self, stream):
        logger.debug('Processing stream %s', stream)
        current_checks = stream.get_current_checks()
        current_watchdogs = stream.get_current_watchdogs()
        active_alerts = self._alerts.get_stream_active_alerts(stream_id=stream.id)
        active_check_alerts = {a.path: a for a in active_alerts if a.alert_type == 'check'}
        active_watchdog_alerts = {a.path: a for a in active_alerts if a.alert_type == 'watchdog'}
        # create/update check alerts
        for path, check in current_checks.items():
            alert = active_check_alerts.get(path)
            if check['state'] == 'green' and alert:
                alert.deactivate()
            elif check['state'] != 'green' and (not alert or check['state'] != alert.severity):
                if alert:
                    alert.deactivate()
                self._alerts.create_alert(
                    alert_type='check',
                    stream_id=stream.id,
                    stream_label=stream.label,
                    path=path,
                    severity=check['state'])
        # deactivate check alerts
        for path, alert in active_check_alerts.items():
            if path not in current_checks:
                alert.deactivate()
        # create/update watchdog alerts
        now = self._system.time_ms()
        for path, watchdog in current_watchdogs.items():
            expired = watchdog['deadline'] <= now
            alert = active_watchdog_alerts.get(path)
            logger.debug('Watchdog path: %r expired: %r alert: %r', path, expired, alert)
            if not expired:
                if alert:
                    alert.deactivate()
            else:
                if not alert:
                    self._alerts.create_alert(
                        alert_type='watchdog',
                        stream_id=stream.id,
                        stream_label=stream.label,
                        path=path,
                        severity='red')
        # deactivate watchdog alerts
        for path, alert in active_watchdog_alerts.items():
            if path not in current_watchdogs:
                alert.deactivate()
