from datetime import datetime
from typing import Union


def now() -> datetime:
    return datetime.now()


def format_timestamp(
    timestamp: datetime, format_string: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    return timestamp.strftime(format_string)


def parse_timestamp(
    timestamp_str: str, format_string: str = "%Y-%m-%d %H:%M:%S"
) -> datetime:
    try:
        return datetime.strptime(timestamp_str, format_string)
    except ValueError:
        return datetime.now()


def ensure_datetime(value: Union[datetime, str, None]) -> datetime:
    if value is None:
        return now()
    if isinstance(value, str):
        return parse_timestamp(value)
    return value
