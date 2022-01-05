import re

from io import StringIO
from lxml import etree
from requests import Session


def scrape(url):
    session = Session()
    response = session.get(url)

    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(response.text), parser)

    links = tree.xpath("//table[@id='aspxroundpanelRecent2_ASPxPanel4_grdEventsRecent2_DXMainTable']/tr[@class='dxgvDataRow_CustomThemeModerno']/td[1]//a")
    for link in links:
        href = link.attrib['href']
        pattern = '.*?\((?P<id>.*?),.*'
        match = re.match(pattern, href)

        link_id = match.group('id')
        event_url = f'https://chaffeecoco.civicclerk.com/Web/Player.aspx?id={link_id}&key=-1&mod=-1&mk=-1&nov=0'

        response = session.get(event_url)

        ## wait on this
        # parse out info from this page

if __name__ == '__main__':
    url = 'https://chaffeecoco.civicclerk.com/web/home.aspx'
    scrape(url)