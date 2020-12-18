from os.path import join, expanduser


def default_user_home():
    return join(
        expanduser('~'),
        '.civic-scraper'
    )
