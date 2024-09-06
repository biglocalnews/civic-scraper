import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
from requests import Session

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache


class PrimeGovSite(base.Site):
    """For each Primegov site, there seems to be multiple API endpoints that can be queried:
    1. (GET) https://[city].primegov.com/api/meeting/search?from=[m/d/y]&to=[m/d/y]
    2. (GET) https://[city].primegov.com/v2/PublicPortal/ListUpcomingMeetings
    2. (GET) https://[city].primegov.com/v2/PublicPortal/ListArchivedMeetings?year=[year]
    3. (POST) https://[city].primegov.com/api/search?
    """

    def __init__(self, url, place=None, state_or_province=None, cache=Cache()):

        self.url = url
        self.base_url = "https://" + urlparse(url).netloc
        self.primegov_instance = urlparse(url).netloc.split(".")[0]
        self.place = place
        self.state_or_province = state_or_province
        self.cache = cache

        self.session = Session()
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
        )

        # Raise an error if a request gets a failing status code
        self.session.hooks = {
            "response": lambda r, *args, **kwargs: r.raise_for_status()
        }

    def create_asset(self, entry, document):

        url = self._get_agenda_url(entry["id"])
        meeting_datetime = datetime.fromisoformat(entry["dateTime"])
        meeting_id = self._get_meeting_id(document["id"])

        e = {
            "url": url,
            "asset_name": entry["title"],
            "committee_name": None,
            "place": self.place,
            "state_or_province": self.state_or_province,
            "asset_type": "Meeting",
            "meeting_date": meeting_datetime.date(),
            "meeting_time": meeting_datetime.time(),
            "meeting_id": meeting_id,
            "scraped_by": f"civic-scraper_{civic_scraper.__version__}",
            "content_type": "html",
            "content_length": None,
        }

        return Asset(**e)

    def _get_agenda_url(self, id):

        return (
            f"{self.base_url}/Portal/MeetingPreview?compiledMeetingDocumentFileId={id}"
        )

    def _get_meeting_id(self, object_id):

        pattern = r"http[s]?:\/\/[www.]?(\S*).primegov.com\/[\S]*"
        match = re.match(pattern, self.url)
        return f"primegov_{match.group(1)}_{object_id}"

    def scrape(self, start_date=None, end_date=None):

        # API requires both start and end dates
        if not start_date or not end_date:
            start_date = (datetime.today() - timedelta(days=30)).strftime("%m/%d/%Y")
            end_date = datetime.today().strftime("%m/%d/%Y")

        response = self.session.get(
            f"{self.base_url}/api/meeting/search?from={start_date}&to={end_date}"
        )

        ac = AssetCollection()

        for meeting in response.json():
            for entry in meeting["templates"]:
                if "Agenda" in entry["title"]:
                    for doc in entry["compiledMeetingDocumentFiles"]:
                        # HTML files have a compileOutputCode of 3
                        if doc["compileOutputType"] == 3:
                            ac.append(self.create_asset(meeting, doc))

        return ac
