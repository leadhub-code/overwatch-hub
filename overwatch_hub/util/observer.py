import logging
from reprlib import repr as smart_repr


logger = logging.getLogger(__name__)


class Event:
    '''
    Known as Publish-subscribe or Observer pattern.
    '''

    def __init__(self):
        self.callbacks = []

    def __repr__(self):
        return '<{cls} callbacks: {cbs!r}>'.format(
            cls=self.__class__.__name__,
            cbs=self.callbacks)

    def subscribe(self, callback):
        '''
        Register new observer
        '''
        self.callbacks.append(callback)

    def fire(self, params):
        '''
        Notify all observers
        '''
        params_str = smart_repr(params)
        if not self.callbacks:
            logger.debug('No callbacks; params: %s', params_str)
        for cb in self.callbacks:
            logger.debug('Calling %s, params: %s'. cb, params_str)
            cb(params)
