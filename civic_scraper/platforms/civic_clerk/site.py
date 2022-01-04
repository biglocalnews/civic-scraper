from io import StringIO
from lxml import etree
from requests import Session


def scrape(url):
    session = Session()
    response = session.get(url)

    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(response.text), parser)
    # breakpoint()

if __name__ == '__main__':
    url = 'https://chaffeecoco.civicclerk.com/web/home.aspx'
    scrape(url)