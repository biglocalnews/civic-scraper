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
from datetime import datetime
import bs4
import requests
from retrying import retry
import csv
from civic_scraper.scrapers.site import Site

# Code

# granicus object class
class GranicusSite(Site):
    """
    An object with the public methods scrape() and download_csv().
    """
    base_url = "granicus.com"

    def __init__(self, subdomain):
        self.url = "https://{}.{}/ViewPublisher.php?view_id=1".format(subdomain, self.base_url)
        self.runtime = str(datetime.date(datetime.utcnow())).replace('-', '')

    # Public interface (used by calling code)
    def scrape(self, start_date, end_date):
        if start_date == '':
            start_date = self.runtime
        if end_date == '':
            end_date = self.runtime
        html = self._get_html()
        soup = self._make_soup(html)
        return self._get_all_docs(soup, subdomain, start_date, end_date)
        
        # TODO: Add date filter
    
    def download_csv(self, metadata, subdomain):
        """
        Downloads a csv file for a given subdomain and url_list.

        Input: A list of lists of metadata
        Output: A csv of metadata
        """

        # Initializing the .csv
        file_name = "{}.csv".format(subdomain)
        file = open(file_name, 'w')
        header = ['place', 'state_or_province', 'meeting_date', 'committee', 'doc_format', 'meeting_id', 'site_type', 'doc_type', 'url']

        # Writing the .csv
        with file:
            write = csv.writer(file)
            write.writerow(header)
            write.writerows(metadata)
    
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
                self.url = "https://{}.{}/ViewPublisher.php?view_id=2".format(subdomain, self.base_url)
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
    def _get_all_docs(self, soup, subdomain, start_date, end_date):
        """
        Given a dictionary and page URL, harvests all of the links and metadata from
        the response to that request.

        Input: soup
        Returns: A list of lists of metadata and doc urls
        """
        # Get metadata
        # rows = soup.find_all(class_="listItem")
        rows = soup.find_all("tr")

        # Initialize outer list
        metadata = []

        for row in rows:
            items = row.find_all("td")
            
            # Initialize item variables in row
            place = subdomain
            state_or_province = None
            meeting_name = None
            date = None
            duration = None
            agenda = None
            minutes = None
            video = None
            audio = None
            video2 = None
            agenda_packet = None
            site_type = "granicus"
            row_list = []

            for item in items:
                
                if re.search(r"Name", str(item)) != None:
                    meeting_name = item.text.strip()
                elif re.search(r"Date", str(item)) != None:
                    date = item.text.strip()
                elif re.search(r"Duration", str(item)) != None:
                    duration = item.text.strip()
                elif item.text.strip() == "Agenda":
                    agenda = str(item.a["href"]).replace("&amp;", "")
                elif item.text.strip() == "Minutes":
                    minutes = str(item.a["href"]).replace("&amp;", "")
                elif item.text.strip() == "Video":
                    video = item.a["onclick"]
                elif item.text.strip() == "MP3 Audio":
                    audio = item.a["href"]
                elif item.text.strip() == "MP4 Video":
                    video2 = item.a["href"]
                elif item.text.strip() == "Agenda Packet":
                    agenda_packet = str(item.a["href"]).replace("&amp;", "")
            
            # Make meeting id
            meeting_id = "{}_{}_{}_{}_{}".format(subdomain, site_type, meeting_name, date, duration)

            # Convert date to int
            try:
                short_date = re.search(r"\D+.*\d{4}", date).group(0)
            except:
                short_date = date
            
            print("short_date: ", short_date)

            try:
                filter_date = int(datetime.strftime(datetime.strptime(short_date, "%b %d, %Y"), "%Y%m%d"))
            except:
                filter_date = int(str(datetime.date(datetime.utcnow())).replace('-', ''))
            
            print("filter_date: ", filter_date)

            # Filter by date
            if int(start_date) <= filter_date <= int(end_date):
           
                # Add agenda to row list
                row_list.append(place)
                row_list.append(state_or_province)
                row_list.append(date)
                row_list.append(meeting_name)
                row_list.append("pdf") # doc_format
                row_list.append(meeting_id)
                row_list.append(site_type)
                row_list.append("agenda") # doc_type
                row_list.append(agenda) # url
                metadata.append(row_list)

                # Add minutes to row list
                row_list = []
                row_list.append(place)
                row_list.append(state_or_province)
                row_list.append(date)
                row_list.append(meeting_name)
                row_list.append("pdf") # doc_format
                row_list.append(meeting_id)
                row_list.append(site_type)
                row_list.append("minutes") # doc_type
                row_list.append(minutes) # url
                metadata.append(row_list)

                # Add video to row list
                row_list = []
                row_list.append(place)
                row_list.append(state_or_province)
                row_list.append(date)
                row_list.append(meeting_name)
                row_list.append("video") # doc_format
                row_list.append(meeting_id)
                row_list.append(site_type)
                row_list.append("video") # doc_type
                row_list.append(video) # url
                metadata.append(row_list)
                
                # Add audio to row list
                row_list = []
                row_list.append(place)
                row_list.append(state_or_province)
                row_list.append(date)
                row_list.append(meeting_name)
                row_list.append("mp3") # doc_format
                row_list.append(meeting_id)
                row_list.append(site_type)
                row_list.append("audio") # doc_type
                row_list.append(audio) # url
                metadata.append(row_list)

                # Add video2 to row list
                row_list = []
                row_list.append(place)
                row_list.append(state_or_province)
                row_list.append(date)
                row_list.append(meeting_name)
                row_list.append("mp4") # doc_format
                row_list.append(meeting_id)
                row_list.append(site_type)
                row_list.append("video") # doc_type
                row_list.append(video2) # url
                metadata.append(row_list)
                
                # Add agenda_packet to row list
                row_list = []
                row_list.append(place)
                row_list.append(state_or_province)
                row_list.append(date)
                row_list.append(meeting_name)
                row_list.append("pdf") # doc_format
                row_list.append(meeting_id)
                row_list.append(site_type)
                row_list.append("agenda_packet") # doc_type
                row_list.append(agenda_packet) # url
                metadata.append(row_list)
        
        return metadata

if __name__ == '__main__':
    subdomain = input("Enter subdomain: ")
    start_date = input("Enter start date (or nothing): ")
    end_date = input("Enter end date (or nothing): ")
    site = GranicusSite(subdomain)
    metadata = site.scrape(start_date=start_date, end_date=end_date)
    site.download_csv(metadata, subdomain)