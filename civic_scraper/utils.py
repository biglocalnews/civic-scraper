from datetime import datetime
from os.path import expanduser, join


def today_local_str():
    return datetime.now().strftime("%Y-%m-%d")


def default_user_home():
    return join(expanduser("~"), ".civic-scraper")
