from datetime import datetime
from os.path import expanduser, join


def today_local_str():
    return datetime.now().strftime("%Y-%m-%d")


def parse_date(date_str, format="%Y-%m-%d"):
    return datetime.strptime(date_str, format)


def dtz_to_dt(dtz):
    return datetime.fromordinal(dtz.toordinal())


def default_user_home():
    return join(expanduser("~"), ".civic-scraper")


def mb_to_bytes(size_mb):
    if size_mb is None:
        return None
    return float(size_mb) * 1048576
