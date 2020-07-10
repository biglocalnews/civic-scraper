"""
TITLE: GranicusSite
AUTHOR: Amy DiPierro
VERSION: 2020-07-06
USAGE: From the command line, type 'python3 granicus.py' Then enter an optional start and end date
        in the form YYMMDD when prompted.

This script scrapes agendas, minutes and other documents and multimedia from Granicus websites.

Input: A granicus subdomain
Returns: A list of documents found on that subdomain in the given time range

"""
# Libraries

import re
import datetime
import bs4
import requests
from retrying import retry
<<<<<<< HEAD:civic_scraper/scrapers/granicus.py
import csv
from civic_scraper.scrapers.site import Site
=======
>>>>>>> master:civic_scraper/granicus_site.py

# Code

# granicus object class
class GranicusSite(Site):
    """
    An object with the public methods scrape() and download_csv().
    """
    base_url = "granicus.com"

    def __init__(self, subdomain):
        self.url = "https://{}.{}/ViewPublisher.php?view_id=1".format(subdomain, self.base_url)
        self.runtime = datetime.datetime.utcnow().strftime("%Y%m%d")

    # Public interface (used by calling code)
    def scrape(self, start_date, end_date):
        if start_date == '':
            start_date = self.runtime
        if end_date == '':
            end_date = self.runtime
        html = self._get_html()
        soup = self._make_soup(html)
        return self._get_all_docs(soup, start_date, end_date)
    
    # Then, we're going to want to make a document class for granicus docs

    # Private methods

    @retry(
        stop_max_attempt_number=3,
        stop_max_delay=30000,
        wait_exponential_multiplier=1000,
        wait_exponential_max=10000
    )
    def _get_html(self):
        """
        Get HTML response.

        Input: Link of the website we want to scrape.
        Returns: HTML of the website as text.
        """
        try:
            response = requests.get(self.url)
            if response.text.strip() == "Page not found.":
                print("Page not found 1")
                self.url = "https://{}.{}/ViewPublisher.php?view_id=2".format(subdomain, self.base_url)
                response = requests.get(self.url)
                if response.text.strip() == "Page not found.":
                    print("Page not found 2")
                    self.url = "https://{}.{}/ViewPublisher.php?view_id=33".format(subdomain, self.base_url)
                    response = requests.get(self.url)
            return response.text
        except:
            print("The url", self.url, "could not be reached.")
            return ""
    
    def _make_soup(self, html):
        """
        Parses the text we've collected

        Input: Text of website
        Returns: Parsed text
        """
        return bs4.BeautifulSoup(html, 'html.parser')
    
    @retry(
        stop_max_attempt_number=3,
        stop_max_delay=30000,
        wait_exponential_multiplier=1000,
        wait_exponential_max=10000
    )
    def _get_all_docs(self, soup, start_date, end_date):
        """
        Given a dictionary and page URL, harvests all of the links and metadata from
        the response to that request.

        Input: soup
        Returns: A list of dicts of metadata and doc urls
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
            row_dict = {}

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
                filter_date = int(datetime.datetime.strftime(datetime.datetime.strptime(short_date, "%b %d, %Y"), "%Y%m%d"))
            elif year is not None:
                filter_date = datetime.date(year, month, day).strftime("%Y%m%d")
            else:
                filter_date = datetime.datetime.utcnow().strftime("%Y%m%d")

            # Make meeting id
            meeting_id = "{}_{}_{}_{}_{}".format(place, scraped_by, committee_name, filter_date, duration)

            # Filter by date
            if int(start_date) <= int(filter_date) <= int(end_date):
           
                # Add agenda to row list
                row_dict['place'] = place
                row_dict['state_or_province'] = state_or_province
                row_dict['meeting_date'] = date
                row_dict['meeting_time'] = None
                row_dict['committee_name'] = committee_name
                row_dict['doc_format'] = 'pdf'
                row_dict['meeting_id'] = meeting_id
                row_dict['scraped_by'] = scraped_by
                row_dict['doc_type'] = 'agenda' # doc_type
                row_dict['url'] = "http:{}".format(agenda) # url
                if agenda is not None:
                    metadata.append(row_dict)

                # Add minutes to row list
                row_dict = {}
                row_dict['place'] = place
                row_dict['state_or_province'] = state_or_province
                row_dict['meeting_date'] = date
                row_dict['meeting_time'] = None
                row_dict['committee_name'] = committee_name
                row_dict['doc_format'] = 'pdf'
                row_dict['meeting_id'] = meeting_id
                row_dict['scraped_by'] = scraped_by
                row_dict['doc_type'] = 'agenda'  # doc_type
                row_dict['url'] = "http:{}".format(minutes)  # url
                if minutes is not None:
                    metadata.append(row_dict)

                # Add video to row list
                row_dict = {}
                row_dict['place'] = place
                row_dict['state_or_province'] = state_or_province
                row_dict['meeting_date'] = date
                row_dict['meeting_time'] = None
                row_dict['committee_name'] = committee_name
                row_dict['doc_format'] = 'video'
                row_dict['meeting_id'] = meeting_id
                row_dict['scraped_by'] = scraped_by
                row_dict['doc_type'] = 'video'  # doc_type
                row_dict['url'] = video  # url
                if video is not None:
                    metadata.append(row_dict)
                
                # Add audio to row list
                row_dict = {}
                row_dict['place'] = place
                row_dict['state_or_province'] = state_or_province
                row_dict['meeting_date'] = date
                row_dict['meeting_time'] = None
                row_dict['committee_name'] = committee_name
                row_dict['doc_format'] = 'mp3'
                row_dict['meeting_id'] = meeting_id
                row_dict['scraped_by'] = scraped_by
                row_dict['doc_type'] = 'audio'  # doc_type
                row_dict['url'] = audio  # url
                if audio is not None:
                    metadata.append(row_dict)

                # Add video2 to row list
                row_dict = {}
                row_dict['place'] = place
                row_dict['state_or_province'] = state_or_province
                row_dict['meeting_date'] = date
                row_dict['meeting_time'] = None
                row_dict['committee_name'] = committee_name
                row_dict['doc_format'] = 'mp4'
                row_dict['meeting_id'] = meeting_id
                row_dict['scraped_by'] = scraped_by
                row_dict['doc_type'] = 'video'  # doc_type
                row_dict['url'] = video2  # url
                if video2 is not None:
                    metadata.append(row_dict)
                
                # Add agenda_packet to row list
                row_dict = {}
                row_dict['place'] = place
                row_dict['state_or_province'] = state_or_province
                row_dict['meeting_date'] = date
                row_dict['meeting_time'] = None
                row_dict['committee_name'] = committee_name
                row_dict['doc_format'] = 'pdf'
                row_dict['meeting_id'] = meeting_id
                row_dict['scraped_by'] = scraped_by
                row_dict['doc_type'] = 'agenda_packet'  # doc_type
                row_dict['url'] = agenda_packet  # url
                if agenda_packet is not None:
                    metadata.append(row_dict)

                # Add captions to row list
                row_dict = {}
                row_dict['place'] = place
                row_dict['state_or_province'] = state_or_province
                row_dict['meeting_date'] = date
                row_dict['meeting_time'] = None
                row_dict['committee_name'] = committee_name
                row_dict['doc_format'] = 'html'
                row_dict['meeting_id'] = meeting_id
                row_dict['scraped_by'] = scraped_by
                row_dict['doc_type'] = 'captions'  # doc_type
                row_dict['url'] = captions  # url
                if captions is not None:
                    metadata.append(row_dict)
        
        return metadata

if __name__ == '__main__':
    subdomain = input("Enter subdomain: ")
    start_date = input("Enter start date (or nothing): ")
    end_date = input("Enter end date (or nothing): ")
    site = GranicusSite(subdomain)
    metadata = site.scrape(start_date=start_date, end_date=end_date)
    print(metadata)