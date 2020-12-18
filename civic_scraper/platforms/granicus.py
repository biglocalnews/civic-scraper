import re
import datetime
import bs4
import requests
from civic_scraper.base import Site
from civic_scraper.base.constants import SUPPORTED_ASSET_TYPES
from civic_scraper.base import AssetCollection


# Granicus object class
class GranicusSite(Site):
    """
    An object with the public method scrape().
    """

    def __init__(self, url):
        std_url = re.sub(r'(?<=view_id=)\d*', "1", url)
        self.url = std_url
        self.runtime = datetime.datetime.utcnow().strftime("%Y%m%d")

    def scrape(self, start_date, end_date, file_size,
               type_list=SUPPORTED_ASSET_TYPES):
        if start_date == '':
            start_date = self.runtime
        if end_date == '':
            end_date = self.runtime
        html = self._get_html()
        soup = self._make_soup(html)
        # TODO: filter by file size
        return self._get_all_assets(soup, start_date, end_date, type_list)

    def _get_html(self):
        """
        Get HTML response.

        Input: Link of the website we want to scrape.
        Returns: HTML of the website as text.
        """
        response = requests.get(self.url)
        if response.text.strip() == "Page not found.":
            print("Page not found 1")
            self.url = re.sub(r'(?<=view_id=)\d*', "2", self.url)
            response = requests.get(self.url)
            if response.text.strip() == "Page not found.":
                print("Page not found 2")
                self.url = re.sub(r'(?<=view_id=)\d*', "33", self.url)
                response = requests.get(self.url)
        return response.text

    def _make_soup(self, html):
        """
        Parses the text we've collected

        Input: Text of website
        Returns: Parsed text
        """
        return bs4.BeautifulSoup(html, 'html.parser')

    def _get_all_assets(self, soup, start_date, end_date, type_list):
        """
        Given a dictionary and page URL, harvests all of the links and metadata
        from the response to that request.

        Input: soup
        Returns: A list of dicts of metadata and asset urls
        """
        # Get metadata
        # rows = soup.find_all(class_="listItem")
        rows = soup.find_all("tr")

        # Initialize outer list
        metadata = []

        for row in rows:
            items = row.find_all("td")
            # Initialize item variables in row
            place = re.search(r"(?<=\//).*(?=\.g)", self.url).group(0)
            state_or_province = None
            committee_name = None
            date = None
            duration = None
            agenda = None
            minutes = None
            video = None
            audio = None
            video2 = None
            agenda_packet = None
            captions = None
            scraped_by = "granicus"
            year = None
            month = None
            day = None
            short_date = None

            for item in items:

                if re.search(r"Name", str(item)) is not None:
                    committee_name = item.text.strip()
                elif re.search(r"Date", str(item)) is not None:
                    date = item.text.strip()
                elif re.search(r"Duration", str(item)) is not None:
                    duration = item.text.strip()
                elif item.text.strip() == "Agenda":
                    agenda = str(item.a["href"]).replace("&amp;", "")
                elif re.search("Minutes", item.text.strip()) is not None:
                    minutes = str(item.a["href"]).replace("&amp;", "")
                elif item.text.strip() == "Video":
                    video = item.a["onclick"]
                elif re.search("MP3", item.text.strip()) is not None:
                    audio = item.a["href"]
                elif re.search("MP4", item.text.strip()) is not None:
                    video2 = item.a["href"]
                elif item.text.strip() == "Agenda Packet":
                    agenda_packet = str(item.a["href"]).replace("&amp;", "")
                elif re.search("Captions|captions", item.text.strip()) is not None:
                    captions = str(item.a["href"])

            # Convert date to int
            if re.search(r"\D+.*\d{4}", str(date)) is not None:
                short_date = re.search(r"\D+.*\d{4}", str(date)).group(0)
            elif re.search(r"(?<=\/)\d{2}$", str(date)) is not None:
                year = int("20{}".format(re.search(r"(?<=\/)\d{2}$", str(date)).group(0)))
                month = int(re.search(r"(?<=\d)\d{2}(?=\/)", str(date)).group(0))
                day = int(re.search(r"(?<=\/)\d{2}(?=\/)", str(date)).group(0))
            else:
                short_date = None

            if short_date is not None:
                filter_date = int(datetime.datetime.strftime(
                    datetime.datetime.strptime(short_date, "%b %d, %Y"), "%Y%m%d")
                )
            elif year is not None:
                filter_date = datetime.date(year, month, day).strftime("%Y%m%d")
            else:
                filter_date = datetime.datetime.utcnow().strftime("%Y%m%d")

            # Make meeting id
            meeting_id = "{}_{}_{}_{}_{}".format(place, scraped_by, committee_name, filter_date, duration)

            # Filter by date
            if int(start_date) <= int(filter_date) <= int(end_date):
                args = (
                    type_list,
                    place,
                    state_or_province,
                    date,
                    committee_name,
                    meeting_id,
                    scraped_by
                )
                self._add_row(*args, asset_type="agenda", url=agenda)
                self._add_row(*args, asset_type="minutes", url=minutes)
                self._add_row(*args, asset_type="video", url=video)
                self._add_row(*args, asset_type="audio", url=audio)
                self._add_row(*args, asset_type="video", url=video2)
                self._add_row(*args, asset_type="captions", url=captions)
                self._add_row(*args, asset_type="agenda_packet", url=agenda_packet)

        return AssetCollection(metadata)

    def _add_row(self, type_list, place,
                 state_or_province, date, committee_name,
                 meeting_id, scraped_by, asset_type, url):
        metadata = []
        if asset_type in type_list:
            row_dict = {}
            row_dict['place'] = place
            row_dict['state_or_province'] = state_or_province
            row_dict['meeting_date'] = date
            row_dict['meeting_time'] = None
            row_dict['committee_name'] = committee_name
            row_dict['meeting_id'] = meeting_id
            row_dict['scraped_by'] = scraped_by
            row_dict['asset_type'] = asset_type  # asset_type
            if url is not None:
                print("url: ", url)
                if asset_type in ['agenda', 'minutes', 'captions']:
                    url = "http:{}".format(url)
                    row_dict['url'] = url
                else:
                    row_dict['url'] = url
                headers = requests.head(url).headers
                row_dict['content_type'] = headers['content-type']
                row_dict['content_length'] = headers['content-length']
                metadata.append(row_dict)
            return row_dict
