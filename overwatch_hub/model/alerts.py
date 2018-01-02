import logging

from .errors import ModelDeserializeError


logger = logging.getLogger(__name__)


class Alerts:

    def __init__(self):
        pass

    def serialize(self, write):
        write(b'Alerts')
        write(b'/Alerts')

    def deserialize(self, read):
        if read() != b'Alerts':
            raise ModelDeserializeError()
        if read() != b'/Alerts':
            raise ModelDeserializeError()
