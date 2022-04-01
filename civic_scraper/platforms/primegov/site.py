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

class PrimeGovSite(base.Site):

    def __init__(self, url, cache=Cache()):
        self.url = url

        self.session = Session()
        self.session.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"

        # Raise an error if a request gets a failing status code
        self.session.hooks = {
            "response": lambda r, *args, **kwargs: r.raise_for_status()
        }

    def create_asset(self, entry):

        e = {
            "url": entry.url,
            "asset_name": entry.title,
            "committee_name": None,
            "place": None,
            "state_or_province": None,
            "asset_type": "Meeting",
            "meeting_date": entry.date,
            "meeting_time": entry.time,
            "meeting_id": self._get_meeting_id(entry.id),
            "scraped_by": f"civic-scraper_{civic_scraper.__version__}",
            "content_type": "txt",
            "content_length": None,
        }

        return Asset(**e)

    def _get_meetings(self):

        response = self.session.get(self.url)
        return response.json()

    def _get_agenda_urls(self, obj):

        if 'templates' not in obj:
            return []

        agendas = []
        for entry in obj['templates']:
            if 'Agenda' in entry['title']:
                for doc in entry['compiledMeetingDocumentFiles']:
                    if doc['compileOutputType'] == 3:
                        agendas.append(f"https://lacity.primegov.com/Portal/MeetingPreview?compiledMeetingDocumentFileId={doc['id']}")

        return agendas

    def _get_meeting_id(self, object_id):

        pattern = r"http[s]?:\/\/[www.]?(\S*).primegov.com\/[\S]*"
        match = re.match(pattern, self.url)
        return f'primegov_{match.group(1)}_{object_id}'

    def get_agenda_items(self, url):

        resp = self.session.get(url)
        event_tree = lxml.html.fromstring(resp.text)

        return event_tree.xpath('//div[@class="meeting-item"]')


    def scrape(self):

        ac = AssetCollection()

        for meeting in self._get_meetings():
            print(meeting['title'], self._get_agenda_urls(meeting))
            for url in self._get_agenda_urls(meeting):
                agenda_items = self.get_agenda_items(url)
                for item in agenda_items:
                    cleaned_string = re.sub('\s+', ' ', item.text_content())
                    print(cleaned_string + '\n')
