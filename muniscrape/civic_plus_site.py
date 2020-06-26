"""
TITLE: CivicPlusSite
AUTHOR: Amy DiPierro
VERSION: 2020-06-26
USAGE: From the command line, type 'python3 civic_plus_site.py'
        then enter a required subdomain and option start date and end date,
        where a subdomain is a string corresponding to the first
        portion of each subdomain and start date and end date are written in the
        form yyyymmdd. Subdomain is required, but start date and end date have default values.

This script scrapes agendas and minutes from CivicPlus Agenda Center websites.
It is an object-oriented rewrite of civicplus.py

Input: A CivicPlus subdomain
Returns: A list of documents found on that subdomain in the given time range

"""
# Libraries

import logging
import re
from datetime import datetime

import bs4
import requests
from retrying import retry

#TODO: Get logger to work
logger = logging.getLogger(__name__)

class CivicPlusSite:
    """
    In its current configuration, the CivicPlusSite object returns a list of all documents
    from a given website in a given date range.
    """
    base_url = "civicplus.com"

    def __init__(self, subdomain):
        self.url = "https://{}.{}/AgendaCenter".format(subdomain, self.base_url)
        self.runtime = str(datetime.date(datetime.utcnow())).replace('-', '')

    # Public interface (used by calling code)
    def scrape(self, start_date, end_date):
        if start_date == '':
            start_date = self.runtime
        if end_date == '':
            end_date = self.runtime
        logger.info("START SCRAPE - {}".format(self.url))
        html = self._get_html()
        soup = self._make_soup(html)
        post_params = self._get_post_params(soup, start_date, end_date)
        document_stubs = self._get_all_docs(post_params)
        filtered_stubs = self._filter_docs(document_stubs, start_date, end_date)
        logger.info("END SCRAPE - {}".format(self.url))
        print(self._make_document_links(filtered_stubs))
        return self._make_document_links(filtered_stubs)

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

    def _get_post_params(self, soup, start_date, end_date):
        """
        Given parsed html text grabs the bits of html -- a year and a cat_id -- needed
        for the POST request. Filters the list by the year in start_date and end_date.

        Input: Parsed text
        Returns: A dictionary of years and cat_ids
        """
        # Make the dictionary
        year_elements = soup.find_all(href=re.compile("changeYear"))
        years_cat_id = {}
        cat_ids = []
        for element in year_elements:
            link = element.attrs['href']
            year = re.search(r"(?<=\()\d{4}(?=,)", link).group(0)
            start_year = re.search(r"^\d{4}", start_date).group(0)
            end_year = re.search(r"^\d{4}", start_date).group(0)
            if start_year <= year <= end_year:
                cat_id = re.findall(r"\d+(?=,.*')", link)[1]
                cat_ids.append(cat_id)
                years_cat_id[year] = cat_ids

        # Remove duplicates
        years_cat_id_2 = {}
        cat_ids_2 = []
        for year in years_cat_id:
            id_list = years_cat_id[year]
            for id in id_list:
                if id not in cat_ids_2:
                    cat_ids_2.append(id)
            years_cat_id_2[year] = cat_ids_2

        return years_cat_id_2

    @retry(
        stop_max_attempt_number=3,
        stop_max_delay=30000,
        wait_exponential_multiplier=1000,
        wait_exponential_max=10000
    )
    def _get_all_docs(self, post_params):
        """
        Given a dictionary and page URL, makes a post request and harvests all of the links from
        the response to that request.

        Input: Dictionary of years and catIDs, page URL for POST request
        Returns: A list of lists of document URL stubs
        """
        page = "{}/UpdateCategoryList".format(self.url)
        # Get links
        all_links = []
        for year in post_params:
            ids = post_params[year]
            for cat_id in ids:
                payload = {'year': year, 'catID': cat_id, 'term': '', 'prevVersionScreen': 'false'}
                try:
                    response = requests.post(page, params=payload)
                    soup = self._make_soup(response.text)
                    end_links = self._get_links(soup)
                    all_links.append(end_links)
                except:
                    print("In get_all_docs: The POST request failed.")

        # Remove lists for which no links have been found
        for list in all_links:
            if list == []:
                all_links.remove(list)
            for stub in list:
                if stub == []:
                    list.remove(stub)
                elif stub == "":
                    list.remove(stub)

        return all_links

    def _get_links(self, soup):
        """
        Make a list of links to documents we want to download

        Input: Parsed text of website
        Returns: The latter portion of links to documents to download
        """

        links = soup.table.find_all('a')
        end_links = []
        for link in links:
            if '/Agenda/' or '/Minutes/' in link.attrs['href']:
                end_links.append(link.get('href'))
                end_links = list(filter(None, end_links))
                for end_link in end_links:
                    if ('true' in end_link) or ('http' in end_link) or ('Previous' in end_link) or ('DocumentCenter' in end_link):
                        end_links.remove(end_link)

        return end_links

    def _filter_docs(self, document_stubs, start_date, end_date):
        """
        Filters documents to the provided date range.

        :param document_stubs: A list of document stubs
        :param start_date: The earliest date of documents to return
        :param end_date: The latest date of documents to return
        :return: A list of document stubs filtered by date range
        """
        filtered_stubs = []
        for list in document_stubs:
            for stub in list:
                if re.search(r"(?<=_)\d{2}(?=\d{6}-)", stub) is None:
                    month = "no_month"
                else:
                    month = re.search(r"(?<=_)\d{2}(?=\d{6}-)", stub).group(0)
                if re.search(r"(?<=_\d{2})\d{2}(?=\d{4}-)", stub) is None:
                    day = "no_day"
                else:
                    day = re.search(r"(?<=_\d{2})\d{2}(?=\d{4}-)", stub).group(0)
                if re.search(r"(?<=\d)\d{4}(?=-)", stub) is None:
                    year = "no_year"
                else:
                    year = re.search(r"(?<=\d)\d{4}(?=-)", stub).group(0)
                date = "{}{}{}".format(year, month, day)
                if "no" in date:
                    continue
                if int(start_date) <= int(date) <= int(end_date):
                    filtered_stubs.append(stub)

        # Remove duplicates
        filtered_stubs_deduped = []
        for stub in filtered_stubs:
            if stub not in filtered_stubs_deduped:
                filtered_stubs_deduped.append(stub)

        return filtered_stubs_deduped

    def _make_document_links(self, document_stubs):
        """
        Combines a base URL and a list of partial document links (document_stubs)
        to make full urls.

        Input: A list of partial document links (document_stubs)
        Returns: A list of full URLs
        """
        url_list = []

        for stub in document_stubs:
            stub = stub.replace("/AgendaCenter", "")
            text = "{}{}".format(self.url, stub)
            url_list.append(text)

        return url_list

if __name__ == '__main__':
    subdomain = input("Enter subdomain: ")
    start_date = input("Enter start date (or nothing): ")
    end_date = input("Enter end date (or nothing): ")
    site = CivicPlusSite(subdomain)
    site.scrape(start_date=start_date, end_date=end_date)
