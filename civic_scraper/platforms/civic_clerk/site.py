import html
import re
import json
import logging
import requests
from datetime import datetime, date
from pathlib import Path
from urllib.parse import urlparse, urljoin, quote # Added quote for URL encoding

import lxml.html
from bs4 import BeautifulSoup
from requests import Session

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_place_and_state_from_url(url):
    """
    Extracts the place and state from a CivicClerk URL.
    Examples:
        https://turlockca.portal.civicclerk.com -> ("turlock", "ca")
        https://jacksonmi.civicclerk.com -> ("jackson", "mi")
        https://alpharettaga.civicclerk.com -> ("alpharetta", "ga")
        https://islamoradafl.portal.civicclerk.com/ -> ("islamorada", "fl")
    """
    from urllib.parse import urlparse
    import re
    netloc = urlparse(url).netloc
    # Remove subdomains like 'www.'
    netloc = netloc.replace('www.', '')
    # Remove .portal. or .civicclerk.com
    if '.portal.' in netloc:
        sub = netloc.split('.portal.')[0]
    else:
        sub = netloc.split('.civicclerk.com')[0]
    # Remove trailing slashes
    sub = sub.strip('/')
    # Extract place and state (last 2 letters are state)
    m = re.match(r"([a-zA-Z]+)([a-zA-Z]{2})$", sub)
    if m:
        place = m.group(1)
        state = m.group(2)
        return place.lower(), state.lower()
    # fallback: just return sub, ''
    return sub.lower(), ''

class CivicClerkSite(base.Site):
    def __init__(self, url, cache=Cache()):
        """
        CivicClerkSite scraper.
        Args:
            url (str): The base URL for the CivicClerk portal.
            cache (Cache): Optional cache object.
        Note:
            Place and state_or_province are now auto-extracted from the URL.
        """
        self.initial_url = url  # User-provided URL
        self.place, self.state_or_province = extract_place_and_state_from_url(url)
        self.cache = cache
        self.resolved_url = url  # For logging, could be extended for redirects

    def get_api_base(self):
        """Return the CivicClerk API base URL for events."""
        site_url = self.initial_url.rstrip('/')
        if ".portal." in site_url:
            domain = site_url.split(".portal.")[0].replace("https://", "")
        else:
            domain = site_url.split(".civicclerk.com")[0].replace("https://", "")
        return f"https://{domain}.api.civicclerk.com/v1/Events"

    def fetch_all_events(self, start_date=None, end_date=None):
        """Fetch all events from the CivicClerk API, optionally filtered by date range."""
        api_base = self.get_api_base()
        all_events = []
        skip = 0
        PAGE_SIZE = 20
        while True:
            params = {
                "$orderby": "startDateTime asc, eventName asc",
                "$top": PAGE_SIZE,
                "$skip": skip
            }
            # Optionally filter by date range
            if start_date:
                params["$filter"] = f"startDateTime ge {start_date}"
            if end_date:
                if "$filter" in params:
                    params["$filter"] += f" and startDateTime le {end_date}"
                else:
                    params["$filter"] = f"startDateTime le {end_date}"
            logger.info(f"Fetching events $skip={skip} from {api_base}")
            resp = requests.get(api_base, params=params)
            resp.raise_for_status()
            data = resp.json()
            events = data.get("value", [])
            if not events:
                break
            all_events.extend(events)
            skip += PAGE_SIZE
        return all_events

    def standardise_asset_url(self, meeting_id, fileId):
        site_url = self.initial_url.rstrip('/')
        return f"{site_url}/event/{meeting_id}/files/agenda/{fileId}"

    def standardise_meeting_url(self, meeting_id):
        site_url = self.initial_url.rstrip('/')
        return f"{site_url}/event/{meeting_id}/overview"

    def extract_event_details(self, event):
        meeting_date_raw = event.get("startDateTime")
        meeting_date = None
        if meeting_date_raw:
            try:
                dt = datetime.fromisoformat(meeting_date_raw.replace('Z', '+00:00'))
                meeting_date = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                meeting_date = meeting_date_raw
        assets = event.get("publishedFiles", [])
        asset_objs = []
        for asset in assets:
            publish_on_raw = asset.get("publishOn")
            if publish_on_raw:
                try:
                    dt = datetime.fromisoformat(publish_on_raw.replace('Z', '+00:00'))
                    asset["publishOn"] = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass
            fileId = asset.get("fileId")
            asset_url = self.standardise_asset_url(event.get("id"), fileId) if fileId is not None else None
            asset_obj = Asset(
                url=asset_url,
                asset_name=asset.get("fileName"),
                committee_name=event.get("eventCategoryName"),
                place=self.place,
                place_name=self.place,  # Could be improved if human-readable name is available
                state_or_province=self.state_or_province,
                asset_type=asset.get("fileType"),
                meeting_date=meeting_date,
                meeting_id=event.get("id"),
                scraped_by="civic_scraper",
                content_type=asset.get("contentType"),
                content_length=asset.get("fileSize")
            )
            asset_objs.append(asset_obj)
        return asset_objs

    def scrape(self, download=True, start_date=None, end_date=None):
        """Scrape meetings and their assets from the CivicClerk site using the API."""
        ac = AssetCollection()
        logger.info(f"Starting to scrape meetings from {self.resolved_url}")
        if start_date or end_date:
            logger.info(f"Date range: Start={start_date}, End={end_date}")
        events = self.fetch_all_events(start_date=start_date, end_date=end_date)
        for event in events:
            assets = self.extract_event_details(event)
            for asset in assets:
                ac.append(asset)
        return ac

