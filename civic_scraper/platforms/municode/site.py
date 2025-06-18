"""
This module provides functionality to scrape meeting information from Municode Meetings websites.
It is specifically built and tested for the URLs listed in the URLS list below. 
Only sites in the URLS list are officially supported for scraping with this code.
# "https://bluffton-sc.municodemeetings.com/",
#"https://tumwater-wa.municodemeetings.com/",
# "https://columbus-ga.municodemeetings.com/",
# "https://hillsborough-nc.municodemeetings.com/",
"""
import os
import sys

# Add project root to sys.path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
import datetime
import logging
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
import hashlib

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache
from civic_scraper.utils import today_local_str

logger = logging.getLogger(__name__)

HEADERS = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
        }
# List of supported URLs
URLS = [
            # "https://bluffton-sc.municodemeetings.com/",
            #"https://tumwater-wa.municodemeetings.com/",
            # "https://columbus-ga.municodemeetings.com/",
            # "https://hillsborough-nc.municodemeetings.com/",
        ]


class MunicodeSite(base.Site):
    def __init__(self, url, place=None, state_or_province=None, cache=Cache()):
        self.url = url
        self.base_url = "https://" + urlparse(url).netloc
        self.place = place
        self.state_or_province = state_or_province
        self.cache = cache

        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
        )
        self.session.hooks = {
            "response": lambda r, *args, **kwargs: r.raise_for_status()
        }

    def generate_meeting_id(self, date, title):
        """
        Generate a unique meeting ID based on date and title.
        """
        base_str = f"{date}_{title}"
        return hashlib.md5(base_str.encode("utf-8")).hexdigest()
    
        

        

    def fetch_meeting_data(self,url):
            """Fetch and parse meeting data from a given Municode Meetings URL."""
            logging.info(f"Fetching data from: {url}")

            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                logging.error(f"Error fetching {url}: {e}")
                return []

            try:
                soup = BeautifulSoup(response.text, "html.parser")
                view_content = soup.find("div", class_="view-content")
                if not view_content:
                    logging.warning(f"No content with class 'view-content' found at {url}")
                    return []
                table_soup = BeautifulSoup(view_content.prettify(), "html.parser")

                meeting_info = []
                for row in table_soup.find_all("tr"):
                    temp = {}

                    # Extract Date
                    date_td = row.find("td", attrs={"data-th": "Date"})
                    if date_td:
                        span = date_td.find("span", class_="date-display-single")
                        temp["date"] = span["content"] if span and span.has_attr("content") else date_td.get_text(strip=True)

                    # Extract Meeting Title
                    meeting_td = row.find("td", attrs={"data-th": "Meeting"})
                    if meeting_td:
                        temp["Meeting Title"] = meeting_td.get_text(strip=True)

                    # Generate unique meeting_id
                    temp["meeting_id"] = self.generate_meeting_id(
                        temp.get("date", ""), temp.get("Meeting Title", "")
                    )


                    # Agenda & Packet keys
                    agenda_keys = ["Agenda", "Agendas"]
                    packet_keys = ["Packet", "Packets", "Agenda Packets", "Agenda Packet"]

                    # Agenda links
                    temp["Agenda Links"] = []
                    for key in agenda_keys:
                        td = row.find("td", attrs={"data-th": key})
                        if td:
                            temp["Agenda Links"] = [a["href"] for a in td.find_all("a", href=True)]
                            break

                    # Packet links
                    temp["Packet Links"] = []
                    for key in packet_keys:
                        td = row.find("td", attrs={"data-th": key})
                        if td:
                            temp["Packet Links"] = [a["href"] for a in td.find_all("a", href=True)]
                            break
                    # vedio links
                    temp["vedio Links"] = []
                    video_td = row.find("td", attrs={"data-th": "Video"})
                    if video_td:
                        temp["vedio Links"] = [a["href"] for a in video_td.find_all("a", href=True)]

                    if temp:
                        meeting_info.append(temp)

                return meeting_info

            except Exception as e:
                logging.error(f"Error parsing HTML for {url}: {e}")
                return []
            
    def build_asset_data(self, meeting_info, place=None, state_or_province=None):
        """
        Build asset data from parsed meeting info.

        Args:
            meeting_info (list): List of dicts from fetch_meeting_data.
            place (str): Place name.
            state_or_province (str): State or province.

        Returns:
            list: List of asset dicts.
        """
        assets = []
        for row in meeting_info:
            if "CANCELED" in row.get("Meeting Title", "").upper():
                logging.info(f"Skipping cancelled meeting: {row.get('Meeting Title')}")
                continue
            meeting_date = row.get("date")
            meeting_title = row.get("Meeting Title", "")
            meeting_id = row.get("meeting_id")

            # Remove 'meeting' at the end of the title for committee_name
            committee_name = re.sub(r"\s*meeting\s*$", "", meeting_title, flags=re.IGNORECASE)

            scraped_by = f"civic-scraper_{civic_scraper.__version__}"

            
            # adding meeting_info first
            assets.append({
                "meeting_id": meeting_id,
                "state_or_province": state_or_province,
                "place": place,
                "committee_name": committee_name,
                "meeting_title": meeting_title,
                "meeting_date": meeting_date,
                "asset_type": "meeting_info",
                "scraped_by": scraped_by,
                "url": None,  # No URL for meeting info
            })
            # Agenda Links
            for url in row.get("Agenda Links", []):
                assets.append({
                    "meeting_id": meeting_id,
                    "state_or_province": state_or_province,
                    "place": place,
                    "committee_name": committee_name,
                    "meeting_title": meeting_title,
                    "meeting_date": meeting_date,
                    "asset_type": "agenda",
                    "scraped_by": scraped_by,
                    "url": url,
                })
                
            # Packet Links
            for url in row.get("Packet Links", []):
                assets.append({
                    "meeting_id": meeting_id,
                    "state_or_province": state_or_province,
                    "place": place,
                    "committee_name": committee_name,
                    "meeting_title": meeting_title,
                    "meeting_date": meeting_date,
                    "asset_type": "packet",
                    "scraped_by": scraped_by,
                    "url": url,
                })
                
            # Video Links
            for url in row.get("vedio Links", []):
                assets.append({
                    "meeting_id": meeting_id,
                    "state_or_province": state_or_province,
                    "place": place,
                    "committee_name": committee_name,
                    "meeting_title": meeting_title,
                    "meeting_date": meeting_date,
                    "asset_type": "video",
                    "scraped_by": scraped_by,
                    "url": url,
                })
                
            
        return assets

import json
if __name__ == "__main__":
    # Example usage and test for supported URLs
    test_urls = [
        # Uncomment one of the supported URLs to test
        #"https://bluffton-sc.municodemeetings.com/",
        # "https://tumwater-wa.municodemeetings.com/",
        # "https://columbus-ga.municodemeetings.com/",
         "https://hillsborough-nc.municodemeetings.com/",
    ]
    for url in test_urls:
        print(f"Testing MunicodeSite for: {url}")
        site = MunicodeSite(url)
        meeting_info = site.fetch_meeting_data(url)
        print(f"Found {len(meeting_info)} meetings.")
        assets = site.build_asset_data(meeting_info, place=site.place, state_or_province=site.state_or_province)
        print(f"Extracted {len(assets)} assets.")
        # Print first asset as a sample
        if assets:
            print("Sample asset:", json.dumps(assets,indent=4)) 



