import logging
from time import time


logger = logging.getLogger(__name__)


class System:
    '''
    Abstraction of interactions with operating system, so it be replaced with
    mock/fake object in tests.
    '''

    def time_ms(self):
        return int(time() * 1000)
