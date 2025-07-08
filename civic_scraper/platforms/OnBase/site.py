import re
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Ensure the parent civic_scraper package is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache

class OnBaseSite(base.Site):
    """
    Scraper for OnBase sites.
    """

    def __init__(self, url, place=None, state_or_province=None, cache=None):
        self.url = url
        parsed_url = urlparse(url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.place = place
        self.state_or_province = state_or_province
        self.cache = cache if cache is not None else Cache()
        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )

    def scrape(self, download=True):
        ac = AssetCollection()
        raw_html = self._get_meetings_html()
        if not raw_html:
            return ac

        soup = BeautifulSoup(raw_html, "html.parser")
        meetings_container = soup.find("div", id="meetings-list")
        if not meetings_container:
            meetings_container = soup.body

        if not meetings_container:
            return ac

        meetings = self._extract_meetings(str(meetings_container))

        for meeting in meetings:
            for link in meeting.get("links", []):
                asset_name = link.get("text", "asset")
                asset_url = link.get("url")
                asset = self.create_asset(meeting, asset_name, asset_url)
                ac.append(asset)

        if download and len(ac) > 0:
            asset_dir = Path(self.cache.path, "assets")
            asset_dir.mkdir(parents=True, exist_ok=True)
            for asset in ac:
                if asset.url:
                    # Optionally set a default content_type if None
                    if asset.content_type is None:
                        asset.content_type = "application/octet-stream"
                    asset.download(target_dir=str(asset_dir), session=self.session)

        return ac

    def _get_meetings_html(self):
        try:
            response = self.session.get(self.url, timeout=20)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {self.url}: {e}")
            return None

    def _extract_meetings(self, outer_html):
        soup = BeautifulSoup(outer_html, "html.parser")
        meetings = []
        for row in soup.select("tr.meeting-row"):
            meeting = {}
            # Use data-sortable-type for robust extraction
            for td in row.find_all("td"):
                sortable_type = td.get("data-sortable-type")
                if sortable_type == "mtgName":
                    meeting["meeting_name"] = td.get_text(strip=True)
                elif sortable_type == "mtgType":
                    meeting["meeting_type"] = td.get_text(strip=True)
                elif sortable_type == "mtgTime":
                    meeting["meeting_datetime"] = td.get_text(strip=True)
                    # Optionally, also get the raw sortable-data attribute
                    meeting["meeting_datetime_raw"] = td.get("data-sortable-data")
            # Extract links (Agenda, PDF, Media, etc.) from all <a> tags in the row
            links = []
            for a in row.find_all("a", href=True):
                links.append({
                    "text": a.get_text(strip=True),
                    "url": urljoin(self.base_url, a["href"])
                })
            meeting["links"] = links
            meetings.append(meeting)
        return meetings

    def _get_meeting_id(self, meeting_info):
        instance = urlparse(self.url).netloc.split(".")[0]
        title = re.sub(r"\W+", "-", meeting_info.get("meeting_name", "untitled").strip()).lower()
        dt = meeting_info.get("meeting_datetime_raw") or meeting_info.get("meeting_datetime") or str(datetime.now())
        dt = re.sub(r"\W+", "", dt)
        return f"onbase_{instance}_{title}_{dt}"

    def create_asset(self, meeting_info, asset_name, asset_url):
        dt_str = meeting_info.get("meeting_datetime_raw") or meeting_info.get("meeting_datetime")
        meeting_datetime = None
        if dt_str:
            # Try parsing as timestamp, then as string
            try:
                # If it's a Unix timestamp
                if dt_str.isdigit():
                    meeting_datetime = datetime.fromtimestamp(int(dt_str))
                else:
                    meeting_datetime = datetime.fromisoformat(dt_str)
            except Exception:
                try:
                    meeting_datetime = datetime.strptime(dt_str, "%m/%d/%Y %I:%M:%S %p")
                except Exception:
                    meeting_datetime = None

        if not meeting_datetime:
            meeting_datetime = datetime.now()

        asset_data = {
            "url": asset_url,
            "asset_name": asset_name,
            "committee_name": meeting_info.get("meeting_type", "Unknown Committee"),
            "place": self.place,
            "state_or_province": self.state_or_province,
            "asset_type": "Meeting",
            "meeting_date": meeting_datetime.date(),
            "meeting_time": meeting_datetime.time(),
            "meeting_id": self._get_meeting_id(meeting_info),
            "scraped_by": f"civic-scraper_{getattr(civic_scraper, '__version__', 'unknown')}",
            "content_type": None,
            "content_length": None,
        }
        return Asset(**asset_data)

if __name__ == "__main__":
    urls = [
        "https://agendaonline.mymanatee.org/OnBaseAgendaOnline/Meetings/Search?dropid=11&mtids=107&dropsv=01%2F01%2F2021%2000%3A00%3A00&dropev=01%2F01%2F2040%2000%3A00%3A00",
        "https://www.modestogov.com/749/City-Council-Agendas-Minutes",
        "https://meetings.cob.org/",
        "https://boccmeetings.jocogov.org/onbaseagendaonline",
        "https://agendaonline.mymanatee.org/OnBaseAgendaOnline/",
        "https://meetings.cityofwestsacramento.org/OnBaseAgendaOnline",
    ]
    import json
    for url in urls:
        site = OnBaseSite(url)
        ac = site.scrape()
        print(ac)