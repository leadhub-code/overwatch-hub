from calendar import timegm
from datetime import datetime
import re


_re_date_with_microseconds = re.compile(r'^[0-9]{4}-[012][0-9]-[0123][0-9]T[0-5][0-9]:[0-5][0-9]:[0-5][0-9]\.[0-9]{6}Z?$')


def parse_date(date_str):
    if not isinstance(date_str, str):
        raise Exception('Must be str')
    if _re_date_with_microseconds.match(date_str):
        return datetime.strptime(date_str.rstrip('Z'), '%Y-%m-%dT%H:%M:%S.%f')
    raise Exception('Unsupported date format: {!r}'.format(date_str))


def date_to_timestamp_ms(dt):
    ts = timegm(dt.utctimetuple())
    return int(ts) * 1000 + dt.microsecond // 1000


def parse_date_to_timestamp_ms(date_str):
    dt = parse_date(date_str)
    return date_to_timestamp_ms(dt)


assert parse_date(datetime.utcnow().isoformat())
