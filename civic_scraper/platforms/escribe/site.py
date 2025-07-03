import logging
import civic_scraper
from bs4 import BeautifulSoup
from typing import Optional, List
import requests
import os
from datetime import datetime
import json
import re
from urllib.parse import urljoin

try:
    from civic_scraper.base.site import Site as BaseSite
    from civic_scraper.base.asset import AssetCollection
    from civic_scraper.base.cache import Cache
    from civic_scraper.base.asset import Asset
except ImportError:
    # Fallback minimal definitions
    class BaseSite:
        def __init__(self, url: str, *, place: Optional[str] = None, state_or_province: Optional[str] = None,
                     cache: Optional[Cache] = None, parser_kls=None, committee_id: Optional[str] = None,
                     timezone: Optional[str] = None, **kwargs):
            self.url = url
        def _fetch_html(self, url: str) -> str:
            return ""
    class AssetCollection(list):
        pass
    class Cache:
        pass
    class Asset:
        pass

logger = logging.getLogger(__name__)

class EscribeSite(BaseSite):
    """
    Scraper for Escribe-powered meeting portals.
    Extracts committee types and meeting listings for each type.
    """
    def __init__(self, url: str, *, place: Optional[str] = None,
                 state_or_province: Optional[str] = None,
                 cache: Optional[Cache] = None,
                 committee_names: Optional[List[str]] = None,
                 timezone: Optional[str] = None,
                 **kwargs):
        # Normalize URL: remove ?Year=YYYY if present
        import re
        url = re.sub(r'[?&]Year=\d{4}$', '', url)
        # Also remove trailing ? if left
        url = re.sub(r'[?]$', '', url)
        super().__init__(url, place=place, state_or_province=state_or_province,
                         cache=cache, parser_kls=None, timezone=timezone, **kwargs)
        self.committee_names = committee_names or []
        # Use a session with a browser-like User-Agent to avoid 403 forbidden
        self.session = requests.Session()
        # Use browser-like and AJAX headers to avoid server errors
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/117.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': self.url.rstrip('/'),
            'Content-Type': 'application/json; charset=utf-8'
        })


    def scrape(self, start_date: Optional[str] = None,
               end_date: Optional[str] = None,
               **kwargs) -> AssetCollection:
        """
        Scrape all meetings for the given committees, then filter by date range.
        """
        logger.info(f"Starting Escribe scrape for URL: {self.url}")
        all_assets = AssetCollection()
        committees = self.committee_names or []
        meetings_all = []
        meeting_keys = set()
        # 1. Scrape all available meetings for each committee (across all years in range)
        for committee in committees:
            logger.info(f"Scraping committee: {committee}")
            for year in range(2015, datetime.now().year + 2):
                post_url = self.url.rstrip('/') + f'/MeetingsCalendarView.aspx/PastMeetings?Year={year}'
                payload = {"type": committee}
                try:
                    resp = self.session.post(post_url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    meetings = data.get("d", [])
                    logger.info(f"Found {len(meetings)} meetings for {committee} in {year}")
                    for meeting in meetings:
                        if meeting.get("MeetingType") == committee:
                            # Use a tuple of (committee, FormattedStart, MeetingTitle/Title/MeetingId) as a unique key
                            key = (
                                committee,
                                meeting.get("FormattedStart"),
                                meeting.get("Title") or meeting.get("MeetingTitle") or meeting.get("MeetingId") or ""
                            )
                            if key not in meeting_keys:
                                meeting_keys.add(key)
                                meetings_all.append((committee, meeting))
                except Exception as e:
                    logger.warning(f"Failed to fetch meetings for {committee} in {year}: {e}")

        # 2. Filter meetings by input date range
        filtered_meetings = []
        for committee, meeting in meetings_all:
            meeting_date = meeting.get("FormattedStart")
            meeting_date_obj = None
            if meeting_date:
                date_match = re.search(r"([A-Za-z]+, )?([A-Za-z]+ \d{1,2}, \d{4})(?: @ ([0-9: ]+[APMapm]{2}))?", meeting_date)
                if date_match:
                    date_part = date_match.group(2)
                    time_part = date_match.group(3)
                    dt_str = date_part
                    if time_part:
                        dt_str = f"{date_part} {time_part}"
                    for fmt in ["%B %d, %Y %I:%M %p", "%B %d, %Y"]:
                        try:
                            meeting_date_obj = datetime.strptime(dt_str, fmt)
                            break
                        except Exception:
                            continue
            if not meeting_date_obj:
                continue
            # Filter by start_date and end_date
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    if not (start_dt <= meeting_date_obj <= end_dt):
                        continue
                except Exception:
                    continue
            filtered_meetings.append((committee, meeting, meeting_date))

        # 3. Parse as json asset
        for committee, meeting, meeting_date in filtered_meetings:
            seen_docs = set()
            # Parse meeting_date_obj again for formatting
            meeting_date_obj = None
            if meeting_date:
                date_match = re.search(r"([A-Za-z]+, )?([A-Za-z]+ \d{1,2}, \d{4})(?: @ ([0-9: ]+[APMapm]{2}))?", meeting_date)
                if date_match:
                    date_part = date_match.group(2)
                    time_part = date_match.group(3)
                    dt_str = date_part
                    if time_part:
                        dt_str = f"{date_part} {time_part}"
                    for fmt in ["%B %d, %Y %I:%M %p", "%B %d, %Y"]:
                        try:
                            meeting_date_obj = datetime.strptime(dt_str, fmt)
                            break
                        except Exception:
                            continue
            # Compose asset_name as 'Month date, year - committee_name'
            asset_date_str = meeting_date_obj.strftime("%B %d, %Y") if meeting_date_obj else meeting_date
            meeting_time = None
            if meeting_date_obj and date_match and date_match.group(3):
                meeting_time = date_match.group(3)
            meeting_id = meeting.get("MeetingId") or meeting.get("Id") or None
            place_name = self.place
            for doc in meeting.get("MeetingLinks", []) + meeting.get("AdditionalDocumentsLinks", []):
                doc_url = doc.get("Url")
                if doc_url and not doc_url.startswith("http"):
                    doc_url = urljoin(self.url, doc_url)
                # Asset type from doc title or url
                doc_title = doc.get("Title", "Document")
                # Try to infer asset_type from doc_title (e.g., Minutes, Agenda, Video, etc.)
                asset_type = None
                doc_title_lower = doc_title.lower()
                if "minute" in doc_title_lower:
                    asset_type = "Minutes"
                elif "agenda" in doc_title_lower:
                    asset_type = "Agenda"
                elif "video" in doc_title_lower:
                    asset_type = "Video"
                elif "recommendation" in doc_title_lower:
                    asset_type = "Recommendation"
                else:
                    asset_type = doc_title
                # Compose asset_name as 'Month date, year - committee_name'
                asset_name = f"{asset_date_str} - {committee}"
                doc_key = (doc_url, asset_name, asset_type)
                if doc_url and doc_key not in seen_docs:
                    seen_docs.add(doc_key)
                    all_assets.append(Asset(
                        asset_name=asset_name,
                        url=doc_url,
                        meeting_date=meeting_date,
                        committee_name=committee,
                        place=self.place,
                        place_name=place_name,
                        state_or_province=self.state_or_province,
                        asset_type=asset_type,
                        meeting_time=meeting_time,
                        meeting_id=meeting_id,
                        scraped_by=f"civic-scraper_{getattr(civic_scraper, '__version__', 'unknown')}",
                        content_type=None,
                        content_length=None
                    ))
        return all_assets


    def _extract_meeting_types(self, html_content: str) -> List[str]:
        """
        Parse the initial page HTML to list all meeting types/panels available.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        container = soup.find('div', class_='past-meetings-region')
        if not container:
            logger.warning("EscribeSite: no past-meetings-region found in HTML")
            return []
        types: List[str] = []
        for mt in container.find_all('div', class_='MeetingTypeList'):
            name_tag = mt.find('span', class_='MeetingTypeNameText')
            if name_tag:
                name = name_tag.get_text(strip=True).rstrip('\xa0')
                types.append(name)
        return types
