import re

from datetime import datetime
from io import StringIO
from lxml import etree
from requests import Session

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache


class CivicClerkSite(base.Site):
    def __init__(self, url, place=None, state_or_province=None, cache=Cache()):
        self.url = url
        self.place = place
        self.state_or_province = state_or_province
        self.cache = cache

    def create_asset(self, asset, committee_name, meeting_datetime, meeting_id):
        asset_base_url = "https://chaffeecoco.civicclerk.com/"
        asset_url, asset_name = asset
        asset_type = 'Meeting'
        full_asset_url = asset_base_url + asset_url[2:]

        e = {'url': full_asset_url,
             'asset_name': asset_name,
             'committee_name': committee_name,
             'place': None,
             'state_or_province': None,
             'asset_type': asset_type,
             'meeting_date': meeting_datetime.date(),
             'meeting_time': meeting_datetime.time(),
             'meeting_id': meeting_id,
             'scraped_by': f'civic-scraper_{civic_scraper.__version__}',
             'content_type': 'txt',
             'content_length': None,
            }
        return Asset(**e)

    def scrape(self, download=True):
        session = Session()
        response = session.get(self.url)

        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(response.text), parser)

        # only the first <=10 events are here; pagination to be handled later
        events = tree.xpath("//table[@id='aspxroundpanelRecent2_ASPxPanel4_grdEventsRecent2_DXMainTable']/tr[@class='dxgvDataRow_CustomThemeModerno']")

        ac = AssetCollection()

        for event in events:
            # grab commitee name, link, & time/date from row
            committee_name = event.xpath("./td[1]//text()")[1].strip()
            str_datetime = event.xpath("./td[2]//text()")[0].strip()
            meeting_datetime = datetime.strptime(str_datetime, '%m/%d/%Y %I:%M %p')

            # for link in row, scrape all assets
            link = event.xpath("./td[1]//a")[0]
            href = link.attrib['href']
            pattern = '.*?\((?P<id>.*?),.*'
            match = re.match(pattern, href)

            meeting_id = match.group('id')
            event_url = f'https://chaffeecoco.civicclerk.com/Web/DocumentFrame.aspx?id={meeting_id}&mod=-1&player_tab=-2'
            event_response = session.get(event_url)

            event_tree = etree.parse(StringIO(event_response.text), parser)
            event_frame = event_tree.xpath("//iframe")[0].attrib['src']

            event_frame_url = 'https://chaffeecoco.civicclerk.com' + event_frame
            frame_response = session.get(event_frame_url)
            frame_tree = etree.parse(StringIO(frame_response.text), parser)

            agenda_items = frame_tree.xpath("//tr[./td[@class='dx-wrap dxtl dxtl__B0' and not(@colspan)]]")
            for item in agenda_items:
                link_tr_text = item.xpath("./following-sibling::tr[1]")[0]
                link_tr = [(tr.attrib['href'], tr.xpath("./text()")[0]) for tr in link_tr_text.xpath(".//a") if tr.attrib['href'] != '#']
                if link_tr:
                    assets = [self.create_asset(a, committee_name, meeting_datetime, meeting_id) for a in link_tr]
                    for a in assets:
                        ac.append(a)

            agenda_name = frame_tree.xpath("//span[@id='lblAgendaName']")

            if download:
                asset_dir = Path(self.cache.path, 'assets')
                asset_dir.mkdir(parents=True, exist_ok=True)
                for asset in ac:
                    if asset.url:
                        dir_str = str(asset_dir)
                        asset.download(target_dir=dir_str, session=session)

            # breakpoint()

            ## wait on this
            # parse out info from this page
        return ac

if __name__ == '__main__':
    url = 'https://chaffeecoco.civicclerk.com/web/home.aspx'
    scraper = CivicClerkSite(url)
    scraper.scrape()