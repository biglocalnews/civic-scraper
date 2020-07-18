"""
TITLE: CivicPlusSite
AUTHOR: Amy DiPierro
VERSION: 2020-07-16

This module scrapes agendas and minutes from CivicPlus Agenda Center websites. It has one public method, scrape(),
which returns a AssetList object.

From CLI:
        From the command line, type 'python3 civicplus.py'
        then enter a required url and optional start_date, end_date,
        file_size and type_list as defined below.

From Python:
        site = CivicPlusSite(base_url) # creates a CivicPlusSite object
        site.scrape(start_date, end_date, file_size, type_list)

Inputs of scrape():
        url: str of the form 'https://*.civicplus.com/AgendaCenter', where * is a string specific to the website.
        start_date: str entered in the form YYYYMMDD
        end_date: str entered in the form YYMMDD
        file_size: int size of file in gigabytes
        type_list: list of strings with one or more possible file types to download

Returns of scrape(): AssetList object.

"""
# Libraries

import re
from datetime import datetime
from datetime import time
from datetime import date
import bs4
import requests
from civic_scraper.scrapers.site import Site

from civic_scraper.asset import Asset, AssetCollection
SUPPORTED_ASSET_TYPES = ['agenda', 'minutes', 'audio', 'video', 'video2', 'agenda_packet', 'captions']


class CivicPlusSite(Site):
    """
    In its current configuration, the CivicPlusSite object returns a AssetList object
    corresponding to the date range and URL that has been entered.
    """

    def __init__(self, base_url):
        """
        Creates a CivicPlusSite object

        Input: URL of the form 'https://*.civicplus.com/AgendaCenter', where * is a string specific to the website.
        """
        self.url = base_url
        self.runtime = str(datetime.date(datetime.utcnow())).replace('-', '')

    # Public interface (used by calling code)
    def scrape(
            self,
            start_date,
            end_date,
            file_size_filter=100,
            file_type_filter=SUPPORTED_ASSET_TYPES,

    ):
        """
        Input: start_date: str entered in the form YYYYMMDD
                end_date: str entered in the form YYMMDD
                file_size_filter: int size of file in gigabytes
                file_type_filter: list of strings with one or more possible
                file
                types to
                download

        Returns: AssetList object
        """
        # TODO: think about workflow here. It may make make more sense for
        #  the filtering on file type etc. to be applied at a downstream stage
        #  like AssetList.download() than at the scraping stage itself. (It's
        #  not costly to list the metadata for a big file, but it's costly
        #  to automatically download big files)

        # TODO: if the goal is to have a reasonable default maximum file
        #  size to prevent accidentally starting large downloads, the default
        #  should be in the range of 10-100 MB, not 100 GB. It might make
        #  more sense for the units to be MB as well.

        # TODO: for type_list and file_size, make it possible NOT to apply
        #  the filters - so that if I don't want to filter, I don't
        #  have to. One option: if file_size_filter is None, don't filter by
        #  file size.

        if start_date == '':
            start_date = self.runtime
        if end_date == '':
            end_date = self.runtime
        html = self._get_html()
        soup = self._make_soup(html)
        post_params = self._get_post_params(soup, start_date, end_date)
        asset_stubs = self._get_all_assets(post_params)
        filtered_stubs = self._filter_assets(asset_stubs, start_date, end_date)
        links = self._make_asset_links(filtered_stubs)
        file_size_filter = self._gb_to_bytes(file_size_filter)
        metadata = self._get_metadata(links, file_size_filter,
                                      file_type_filter)
        return metadata

    # Private methods

    def _get_metadata(self, url_list, file_size, type_list):
        """
        Returns a list of AssetList objects.

        Input: A list of URLs, a file_size limit (int), a list of asset types
        Output: A AssetList object
        """

        assets = []

        for link in url_list:
            asset_args = {}
            asset_args['place'] = self._get_asset_metadata(r"(?<=-)\w+(?=\.)", link)
            asset_args['state_or_province'] = self._get_asset_metadata(r"(?<=//)\w{2}(?=-)", link)
            meeting_date = self._get_asset_metadata(r"(?<=_)\w{8}(?=-)", link)
            asset_args['meeting_date'] = date(int(meeting_date[4:]), int(meeting_date[:2]), int(meeting_date[2:4]))
            asset_args['meeting_time'] = time()
            asset_args['committee_name'] = None
            asset_args['meeting_id'] = link
            asset_type = self._get_asset_metadata(r"(?<=e/)\w+(?=/_)", link)
            asset_args['asset_type'] = asset_type.lower()
            asset_args['url'] = link
            asset_args['scraped_by'] = 'civicplus.py_v2020-07-09'
            headers = requests.head(link).headers
            asset_args['content_type'] = headers['content-type']
            asset_args['content_length'] = headers['content-length']
            if asset_args['asset_type'] in type_list and int(headers['content-length']) <= int(file_size):
                assets.append(Asset(**asset_args))

        return AssetCollection(assets)

    def _get_html(self):
        """
        Get HTML response.

        Input: Link of the website we want to scrape.
        Returns: HTML of the website as text.
        """
        response = requests.get(self.url)
        return response.text

    def _make_soup(self, html):
        """
        Parses the text we've collected

        Input: Text of website
        Returns: Parsed text
        """
        return bs4.BeautifulSoup(html, 'html.parser')

    def _get_post_params(self, soup, start, end):
        """
        Given parsed html text grabs the bits of html -- a year and a cat_id -- needed
        for the POST request. Filters the list by the year in start_date and end_date.

        Input: Parsed text, start date (YYYYMMDD) and end date (YYYYMMDD)
        Returns: A dictionary of years and cat_ids
        """
        # Make the dictionary
        year_elements = soup.find_all(href=re.compile("changeYear"))
        years_cat_id = {}
        cat_ids = []
        for element in year_elements:
            link = element.attrs['href']
            year = re.search(r"(?<=\()\d{4}(?=,)", link).group(0)
            start_year = re.search(r"^\d{4}", start).group(0)
            end_year = re.search(r"^\d{4}", end).group(0)
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

    def _get_all_assets(self, post_params):
        """
        Given a dictionary and page URL, makes a post request and harvests all of the links from
        the response to that request.

        Input: Dictionary of years and catIDs, page URL for POST request
        Returns: A list of lists of asset URL stubs
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
                    print("In get_all_assets: The POST request failed.")

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
        Make a list of links to assets we want to download

        Input: Parsed text of website
        Returns: The latter portion of links to assets to download
        """

        links = soup.table.find_all('a')
        end_links = []
        for link in links:
            if '/Agenda/' or '/Minutes/' in link.attrs['href']:
                end_links.append(link.get('href'))
                end_links = list(filter(None, end_links))
                for end_link in end_links:
                    if ('true' in end_link) or ('http' in end_link) or ('Previous' in end_link) or ('AssetCenter' in end_link):
                        end_links.remove(end_link)

        return end_links

    def _filter_assets(self, asset_stubs, start, end):
        """
        Filters assets to the provided date range.

        Inputs:
        asset_stubs: A list of asset stubs
        start: The earliest date of assets to return
        end: The latest date of assets to return
        Returns: A list of asset stubs filtered by date range
        """
        filtered_stubs = []
        for list in asset_stubs:
            for stub in list:
                if re.search(r"(?<=_)\d{2}(?=\d{6}-)", stub) is None:
                    month = datetime.utcnow().month
                else:
                    month = re.search(r"(?<=_)\d{2}(?=\d{6}-)", stub).group(0)
                if re.search(r"(?<=_\d{2})\d{2}(?=\d{4}-)", stub) is None:
                    day = datetime.utcnow().day
                else:
                    day = re.search(r"(?<=_\d{2})\d{2}(?=\d{4}-)", stub).group(0)
                if re.search(r"(?<=\d)\d{4}(?=-)", stub) is None:
                    year = datetime.utcnow().year
                else:
                    year = re.search(r"(?<=\d)\d{4}(?=-)", stub).group(0)
                date = "{}{}{}".format(year, month, day)
                if "no" in date:
                    continue
                if int(start) <= int(date) <= int(end):
                    filtered_stubs.append(stub)

        # Remove duplicates
        filtered_stubs_deduped = []
        for stub in filtered_stubs:
            if stub not in filtered_stubs_deduped:
                filtered_stubs_deduped.append(stub)

        return filtered_stubs_deduped

    def _make_asset_links(self, asset_stubs):
        """
        Combines a base URL and a list of partial asset links (asset_stubs)
        to make full urls.

        Input: A list of partial asset links (asset_stubs)
        Returns: A list of full URLs
        """
        url_list = []

        for stub in asset_stubs:
            stub = stub.replace("/AgendaCenter", "")
            text = "{}{}".format(self.url, stub)
            url_list.append(text)

        return url_list

    def _get_asset_metadata(self, regex, asset_link):
        """
        Extracts metadata from a provided asset URL.
        Input: Regex to extract metadata
        Returns: Extracted metadata as a string or "no_data" if no metadata is extracted
        """
        try:
            return re.search(regex, asset_link).group(0)
        except AttributeError as error:
            return "no_data"

    def _gb_to_bytes(self, file_size):
        """
        Converts file_size from gigabytes to bytes.
        Input: File size in gigabytes. Default is 100 GB.
        Returns: File size in bytes.
        """
        return file_size * 1e6

if __name__ == '__main__':
    base_url = input("Enter a CivicPlus url: ")
    start_date = input("Enter start date (or nothing): ")
    end_date = input("Enter end date (or nothing): ")
    site = CivicPlusSite(base_url)
    url_dict = site.scrape(start_date=start_date, end_date=end_date)
    print(url_dict)
