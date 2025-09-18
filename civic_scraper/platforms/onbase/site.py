import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
from civic_scraper.base.site import Site
from civic_scraper.base.asset import Asset, AssetCollection

class OnBaseSite(Site):
    """Scraper for OnBase meeting sites."""
    def scrape(self, start_date: str = None, end_date: str = None, download: bool = False, cache: bool = False, file_size: float = None, asset_list: list = None) -> AssetCollection:
        """
        Scrape the OnBase site for meeting assets between start_date and end_date.
        """
        import requests
        from dateutil import parser as date_parser

        # Fetch the main meetings page
        response = requests.get(self.url)
        response.raise_for_status()
        html = response.text
        all_assets = self.scrape_meetings_from_html(html)

        # Filter by date if specified
        def in_range(asset):
            if not asset.meeting_date:
                return False
            if start_date:
                start = date_parser.parse(start_date).date()
                if asset.meeting_date.date() < start:
                    return False
            if end_date:
                end = date_parser.parse(end_date).date()
                if asset.meeting_date.date() > end:
                    return False
            return True

        filtered_assets = AssetCollection([a for a in all_assets if in_range(a)])
        return filtered_assets

    def scrape_meetings_from_html(self, html: str) -> AssetCollection:
        soup = BeautifulSoup(html, 'html.parser')
        meetings = AssetCollection()
        for row in soup.select('tr.meeting-row'):
            meeting_id = row.get('data-meeting-id')
            tds = row.find_all('td')
            # Meeting name/type/date
            committee_name = tds[0].get_text(strip=True) if len(tds) > 0 else None
            meeting_type = tds[1].get_text(strip=True) if len(tds) > 1 else None
            date_str = tds[2].get('data-sortable-label') if len(tds) > 2 else None
            meeting_date = None
            if date_str:
                try:
                    meeting_date = datetime.datetime.strptime(date_str, '%m/%d/%Y')
                except Exception:
                    meeting_date = None
            # Find asset links (agenda, PDF, etc.)
            for link in row.find_all('a'):
                href = link.get('href')
                title = link.get('title', '').lower()
                asset_type = None
                if 'agenda' in title:
                    asset_type = 'agenda'
                elif 'minutes' in title:
                    asset_type = 'minutes'
                if asset_type and href:
                    asset = Asset(
                        url=href,
                        asset_name=link.get_text(strip=True),
                        committee_name=committee_name,
                        place=self.place,
                        place_name=self.place,
                        state_or_province=self.state_or_province,
                        asset_type=asset_type,
                        meeting_date=meeting_date,
                        meeting_id=meeting_id,
                        scraped_by='onbase-site',
                    )
                    meetings.append(asset)
        return meetings
