import logging
from time import time


logger = logging.getLogger(__name__)


class System:

    def time_ms(self):
        return int(time() * 1000)
