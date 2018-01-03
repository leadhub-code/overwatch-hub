from datetime import datetime, timedelta
from calendar import timegm
import logging
from pathlib import Path
from pytest import fixture
import sys


# logging.basicConfig(
#     format='~ %(asctime)s %(name)-20s %(levelname)5s: %(message)s',
#     stream=sys.stdout,
#     level=logging.DEBUG)


@fixture
def temp_dir(tmpdir):
    # use stdlib Path instead of py.path
    return Path(str(tmpdir))


@fixture
def project_dir():
    return Path(__file__).parent.parent.resolve()


class DeterministicTime:

    def __init__(self, start_date):
        assert isinstance(start_date, datetime)
        self._dt = start_date

    def __repr__(self):
        return '<{cls} {dt}>'.format(cls=self.__class__.__name__, dt=self._dt)

    def time(self):
        return timegm(self._dt.timetuple())

    def advance(self, **kwargs):
        self._dt += timedelta(**kwargs)


@fixture
def deterministic_time():
    dt = datetime.strptime('2018-01-10 12:00:00', '%Y-%m-%d %H:%M:%S')
    return DeterministicTime(dt)


@fixture
def system(deterministic_time):
    class _System:
        def time_ms(self):
            return int(deterministic_time.time() * 1000)
    return _System()
