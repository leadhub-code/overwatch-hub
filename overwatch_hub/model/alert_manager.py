import logging


logger = logging.getLogger(__name__)


class AlertManager:

    def __init__(self, alerts):
        self._alerts = alerts

    def stream_updated(self, params):
        '''
        Handler pro event streams.on_stream_updated
        '''
        self.check_stream(params['stream'])

    def check_stream(self, stream):
        logger.debug('Processing stream %s', stream)
        current_checks = stream.get_current_checks()
        current_watchdogs = stream.get_current_watchdogs()
