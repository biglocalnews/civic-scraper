import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from civic_scraper import __version__
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache
from urllib.parse import urljoin

class ICompassSite(base.Site):
    """
    Scraper for iCompass CivicWeb Portal sites.
    """
    def __init__(self, url, place=None, state_or_province=None, cache=Cache(), committee_names=None):
        self.url = url
        self.cache = cache
        self.place = place
        self.state_or_province = state_or_province
        self.committee_names = committee_names if committee_names is not None else []

    def _get_committee_links(self, driver):
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        committee_links = []
        for a in soup.select('a.meeting-type-item-title'):
            name = a.get_text(strip=True)
            href = a.get('href')
            if href:
                full_url = href if href.startswith('http') else driver.current_url.split('/Portal')[0] + href
                committee_links.append((name, full_url))
        return committee_links

    def _extract_meeting_links(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        meetings = []
        for btn in soup.find_all('button', class_=re.compile(r'meeting-list-item-button')):
            btn_id = btn.get('id', '')
            match = re.search(r'MeetingButton(\d+)', btn_id)
            meeting_id = match.group(1) if match else None
            date_div = btn.find('div', class_='meeting-list-item-button-date')
            date_str = date_div.get_text(strip=True) if date_div else None
            name_divs = btn.find_all('div')
            meeting_name = name_divs[1].get_text(strip=True) if len(name_divs) > 1 else None
            if meeting_id:
                info_url = urljoin(base_url, f'/Portal/MeetingInformation.aspx?Id={meeting_id}')
                meetings.append({
                    'meeting_id': meeting_id,
                    'date': date_str,
                    'name': meeting_name,
                    'info_url': info_url
                })
        return meetings

    def _get_meetings(self, committee_url=None):
        base_url = self.url.split('/Portal')[0]
        print(f"[INFO] Fetching committee page: {committee_url}")
        resp = requests.get(committee_url or self.url, timeout=15)
        if resp.status_code != 200:
            print(f"[WARNING] Failed to fetch committee page {committee_url}: HTTP {resp.status_code}")
            return []
        meetings = self._extract_meeting_links(resp.text, base_url)
        return meetings

    def scrape(self, download=False, start_date=None, end_date=None):
        # Fetch main page and parse committee links
        resp = requests.get(self.url, timeout=15)
        if resp.status_code != 200:
            print(f"[ERROR] Failed to fetch main page {self.url}: HTTP {resp.status_code}")
            return AssetCollection()
        soup = BeautifulSoup(resp.text, 'html.parser')
        committee_links = []
        for a in soup.select('a.meeting-type-item-title'):
            name = a.get_text(strip=True)
            href = a.get('href')
            if href:
                full_url = href if href.startswith('http') else self.url.split('/Portal')[0] + href
                committee_links.append((name, full_url))
        if self.committee_names:
            committee_links = [cl for cl in committee_links if cl[0] in self.committee_names]
        assets = AssetCollection()
        scraped_by = f"civic-scraper_{__version__}"
        # parse start/end date filters
        start_date_obj = datetime.fromisoformat(start_date).date() if start_date else None
        end_date_obj = datetime.fromisoformat(end_date).date() if end_date else None

        # Iterate through committees and meetings
        for name, com_url in committee_links:
            print(f"[INFO] Starting scrape for committee: {name}")
            meetings = self._get_meetings(committee_url=com_url)
            print(f"[INFO] Found {len(meetings)} meetings for committee: {name}")
            for m in meetings:
                info_url = m['info_url']
                print(f"[INFO] Meeting URL: {info_url}")
                # Fetch meeting page to get date
                meeting_date = None
                meeting_time = None
                try:
                    resp_page = requests.get(info_url, timeout=15)
                    if resp_page.status_code == 200:
                        soup_page = BeautifulSoup(resp_page.text, 'html.parser')
                        title_tag = soup_page.find('div', id='ctl00_MainContent_MeetingTitle')
                        title_text = title_tag.get_text(strip=True) if title_tag else ''
                        if '-' in title_text:
                            date_str_page = title_text.split('-')[-1].strip()
                        else:
                            date_str_page = m.get('date')
                        if date_str_page:
                            # Normalize date string (remove commas and title-case month) and try multiple formats
                            date_norm = date_str_page.replace(',', '').title()
                            for fmt in ('%b %d %Y', '%B %d %Y', '%d %b %Y', '%d %B %Y'):
                                try:
                                    meeting_date = datetime.strptime(date_norm, fmt).date()
                                    break
                                except ValueError:
                                    continue
                except Exception as e:
                    print(f"[WARNING] Could not fetch date for {info_url}: {e}")

                meeting_id = f"icompass-{self.place}-{m['meeting_id']}"
                # filter by date if provided
                if meeting_date:
                    if start_date_obj and meeting_date < start_date_obj:
                        print(f"[INFO] Skipping meeting {meeting_id} before start_date {start_date}")
                        continue
                    if end_date_obj and meeting_date > end_date_obj:
                        print(f"[INFO] Skipping meeting {meeting_id} after end_date {end_date}")
                        continue

                asset = Asset(
                    url=info_url,
                    asset_name=m.get('name'),
                    committee_name=name,
                    place=self.place,
                    place_name=None,
                    state_or_province=self.state_or_province,
                    asset_type="meeting_meta_link",
                    meeting_date=meeting_date,
                    meeting_time=meeting_time,
                    meeting_id=meeting_id,
                    scraped_by=scraped_by,
                    content_type="text/url",
                    content_length=None
                )
                assets.append(asset)
        return assets
