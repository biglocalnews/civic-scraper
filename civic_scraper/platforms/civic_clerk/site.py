import re

from datetime import datetime
from io import StringIO
from lxml import etree
from requests import Session
from pathlib import Path
from urllib.parse import urlparse

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache


class CivicClerkSite(base.Site):
    def __init__(self, url, place=None, state_or_province=None, cache=Cache()):
        self.url = url
        self.base_url = 'https://' + urlparse(url).netloc
        self.civicclerk_instance = urlparse(url).netloc.split('.')[0]
        self.place = place
        self.state_or_province = state_or_province
        self.cache = cache

    def create_asset(self, asset, committee_name, meeting_datetime, meeting_id):
        asset_url, asset_name = asset
        asset_type = 'Meeting'
        full_asset_url = self.base_url + asset_url[2:]

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

    def get_meeting_id(self, event):
        link = event.xpath("./td[1]//a")[0]
        href = link.attrib['href']
        pattern = '.*?\((?P<id>.*?),.*'
        match = re.match(pattern, href)
        return (match.group('id'), 'civicclerk_{}_{}'.format(self.civicclerk_instance, match.group('id')))

    def get_agenda_items(self, text, parser, session):
        event_tree = etree.parse(StringIO(text), parser)
        event_frame = event_tree.xpath("//iframe[@id='docViewer']")[0]
        event_frame_url = self.base_url + event_frame.attrib['src']
        frame_response = session.get(event_frame_url)
        frame_tree = etree.parse(StringIO(frame_response.text), parser)

        return frame_tree.xpath("//tr[./td[@class='dx-wrap dxtl dxtl__B0' and not(@colspan)]]")

    def scrape(self, download=True):
        session = Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"})
        response = session.get(self.url)

        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(response.text), parser)

        # only the first <=10 events are here; pagination to be handled later
        events = tree.xpath("//table[@id='aspxroundpanelRecent2_ASPxPanel4_grdEventsRecent2_DXMainTable']/tr[@class='dxgvDataRow_CustomThemeModerno']")

        ac = AssetCollection()

        for event in events:
            committee_name = event.xpath("./td[1]//text()")[1].strip()
            str_datetime = event.xpath("./td[2]//text()")[0].strip()
            meeting_datetime = datetime.strptime(str_datetime, '%m/%d/%Y %I:%M %p')
            meeting_id_num, meeting_id = self.get_meeting_id(event)

            event_url = f'{self.base_url}/Web/DocumentFrame.aspx?id={meeting_id_num}&mod=-1&player_tab=-2'
            event_response = session.get(event_url)

            agenda_items = []
            if event_response.status_code == 200:
                agenda_items = self.get_agenda_items(event_response.text, parser, session)

            for item in agenda_items:
                link_tr_text = item.xpath("./following-sibling::tr[1]")[0]
                link_tr = [(tr.attrib['href'], tr.xpath("./text()")[0]) for tr in link_tr_text.xpath(".//a") if tr.attrib['href'] != '#']
                assets = [self.create_asset(a, committee_name, meeting_datetime, meeting_id) for a in link_tr]
                for a in assets:
                    ac.append(a)

        breakpoint()

        if download:
            asset_dir = Path(self.cache.path, 'assets')
            asset_dir.mkdir(parents=True, exist_ok=True)
            for asset in ac:
                if asset.url:
                    dir_str = str(asset_dir)
                    asset.download(target_dir=dir_str, session=session)
            # parse out info from this page
        return ac
