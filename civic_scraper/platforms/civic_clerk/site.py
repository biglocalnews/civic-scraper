import re
from datetime import datetime
import html
import json
from pathlib import Path
from urllib.parse import urlparse

import demjson
import lxml.html
from requests import Session

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

        self.session = Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"})
        # Raise an error if a request gets a failing status code
        self.session.hooks = {
            'response': lambda r, *args, **kwargs: r.raise_for_status()
        }

    def create_asset(self, asset, committee_name, meeting_datetime, meeting_id):
        asset_url, asset_name = asset
        asset_type = 'Meeting'

        e = {'url': asset_url,
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
        pattern = r'.*?\((?P<id>.*?),.*'
        match = re.match(pattern, href)
        return (match.group('id'), 'civicclerk_{}_{}'.format(self.civicclerk_instance, match.group('id')))

    def get_agenda_items(self, text):
        event_tree = lxml.html.fromstring(text)

        event_frame = event_tree.xpath("//iframe[@id='docViewer']")[0]
        event_frame_url = self.base_url + event_frame.attrib['src']

        frame_response = self.session.get(event_frame_url)
        frame_tree = lxml.html.fromstring(frame_response.text)
        frame_has_table = True if frame_tree.xpath("//table") else False

        assets = []

        if frame_has_table:
            assets_list = frame_tree.xpath("//tr[./td[@class='dx-wrap dxtl dxtl__B0' and not(@colspan)]]")
            for item in assets_list:
                link_tr_text = item.xpath("./following-sibling::tr[1]")[0]
                for tr in link_tr_text.xpath(".//a"):
                    if tr.attrib['href'] != '#':
                        asset_url = self.base_url + '/Web' + tr.attrib['href'][2:]
                        asset_name = tr.xpath("./text()")[0]
                        assets.append((asset_url, asset_name))
        else:
            no_agenda_str = 'Agenda content has not been published for this meeting.'
            if no_agenda_str not in frame_tree.xpath("//text()"):
                assets.append((event_frame_url, None))

        return assets

    def _future_events(self):
        response = self.session.get(self.url)

        tree = lxml.html.fromstring(response.text)

        payload = {}
        payload['__EVENTARGUMENT'] = None
        payload['__EVENTTARGET'] = None
        payload['__VIEWSTATE'] = tree.xpath(
            "//input[@name='__VIEWSTATE']/@value")[0]
        payload['__VIEWSTATEGENERATOR'] = tree.xpath(
            "//input[@name='__VIEWSTATEGENERATOR']/@value")[0]
        payload['__EVENTVALIDATION'] = tree.xpath(
                "//input[@name='__EVENTVALIDATION']/@value")[0]
        payload['__CALLBACKID'] = 'aspxroundpanelCurrent$pnlDetails$grdEventsCurrent'
        #payload['__CALLBACKPARAM'] = 'c0:KV|61;["765","726","859","577","738","652","688","791","766","727"];GB|20;12|PAGERONCLICK3|PBN;'
        payload['__CALLBACKPARAM'] = 'c0:KV|61;["765","726","859","577","738","652","688","791","766","727"];GB|20;12|PAGERONCLICK3|PBN;'
            
        event_callback_source, = tree.xpath('''//script[contains(text(), "var dxo = new ASPxClientGridView('aspxroundpanelCurrent_pnlDetails_grdEventsCurrent');")]/text()''')
        callback_state = demjson.decode(re.search(r'^dxo\.stateObject = \((?P<body>.*)\);$', event_callback_source, re.MULTILINE).group('body'))

        print(callback_state['keys'])
        payload["aspxroundpanelCurrent$pnlDetails$grdEventsCurrent"] = html.escape(json.dumps(callback_state))

        # __CALLBACKPARAM	"c0:KV|61;[\"859\",\"577\",\"738\",\"652\",\"688\",\"791\",\"766\",\"727\",\"860\",\"594\"];GB|20;12|PAGERONCLICK3|PBN;"
        #__CALLBACKPARAM	"c0:KV|61;[\"739\",\"653\",\"767\",\"689\",\"792\",\"579\",\"728\",\"861\",\"777\",\"654\"];GB|20;12|PAGERONCLICK3|PBN;"
        #__CALLBACKPARAM	"c0:KV|31;[\"768\",\"690\",\"793\",\"612\",\"729\"];GB|20;12|PAGERONCLICK3|PN1;"        
        #__CALLBACKPARAM	"c0:KV|61;[\"739\",\"653\",\"767\",\"689\",\"792\",\"579\",\"728\",\"861\",\"777\",\"654\"];GB|20;12|PAGERONCLICK3|PN0;"
        #__CALLBACKPARAM	"c0:KV|61;[\"859\",\"577\",\"738\",\"652\",\"688\",\"791\",\"766\",\"727\",\"860\",\"594\"];GB|20;12|PAGERONCLICK3|PN1;"
        #__CALLBACKPARAM	"c0:KV|61;[\"739\",\"653\",\"767\",\"689\",\"792\",\"579\",\"728\",\"861\",\"777\",\"654\"];GB|20;12|PAGERONCLICK3|PBN;"
        #__CALLBACKPARAM	"c0:KV|61;[\"859\",\"577\",\"738\",\"652\",\"688\",\"791\",\"766\",\"727\",\"860\",\"594\"];GB|20;12|PAGERONCLICK3|PBN;"
        #__CALLBACKPARAM	"c0:KV|61;[\"859\",\"577\",\"738\",\"652\",\"688\",\"791\",\"766\",\"727\",\"860\",\"594\"];GB|20;12|PAGERONCLICK3|PN1;"

        # PBN is next
        while True:

            response = self.session.post(self.url, payload)

            data_str = re.match(r'0\|/\*DX\*/\((?P<body>.*)\)', response.text)\
                         .group('body')

            data = demjson.decode(data_str)

            callback_state = data['result']['stateObject']

            table_tree = lxml.html.fromstring(data['result']['html'])

            payload['__CALLBACKPARAM'] = 'c0:KV|61;' + json.dumps(callback_state['keys']) + ';GB|20;12|PAGERONCLICK3|PBN;'
            payload["aspxroundpanelCurrent$pnlDetails$grdEventsCurrent"] = html.escape(json.dumps(callback_state))
            


            yield table_tree

            breakpoint()
            
        
                       

    def scrape(self, download=True):
        
        list(self._future_events())
        # only the first <=10 events are here; pagination to be handled later
        events = tree.xpath("//table[@id='aspxroundpanelRecent2_ASPxPanel4_grdEventsRecent2_DXMainTable']/tr[@class='dxgvDataRow_CustomThemeModerno']")

        ac = AssetCollection()

        for event in events:
            committee_name = event.xpath("./td[1]//text()")[1].strip()
            str_datetime = event.xpath("./td[2]//text()")[0].strip()
            meeting_datetime = datetime.strptime(str_datetime, '%m/%d/%Y %I:%M %p')
            meeting_id_num, meeting_id = self.get_meeting_id(event)

            event_url = f'{self.base_url}/Web/DocumentFrame.aspx?id={meeting_id_num}&mod=-1&player_tab=-2'
            event_response = self.session.get(event_url)

            agenda_items = self.get_agenda_items(event_response.text)

            if agenda_items:
                assets = [self.create_asset(a, committee_name, meeting_datetime, meeting_id) for a in agenda_items]
                for a in assets:
                    ac.append(a)

        if download:
            asset_dir = Path(self.cache.path, 'assets')
            asset_dir.mkdir(parents=True, exist_ok=True)
            for asset in ac:
                if asset.url:
                    dir_str = str(asset_dir)
                    asset.download(target_dir=dir_str, session=self.session)
            # parse out info from this page
        return ac
