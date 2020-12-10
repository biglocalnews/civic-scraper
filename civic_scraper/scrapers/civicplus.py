"""
TITLE: CivicPlusSite
AUTHOR: Amy DiPierro
VERSION: 2020-10-09

DESCRIPTION: This module scrapes agendas and minutes from CivicPlus Agenda Center websites. It has one public method, scrape(),
which returns an AssetCollection object.

From Python (example):
    base_url = 'http://ab-slavelake.civicplus.com/AgendaCenter'
    site = CivicPlusSite(base_url)
    url_dict = site.scrape(start_date='2020-06-01', target_dir="/Users/amydipierro/GitHub/tmp/", file_size=20, asset_list=['minutes'])

Inputs of scrape():
        start_date: (optional) str entered in the form YYYY-MM-DD.
                    Default is to download all assets back to the earliest asset posted.
        end_date: (optional) str entered in the form YYYY-MM-DD.
                    Default is to download all assets up to the most-recent asset posted.
        download: (optional) bool, True to download assets identified by scraper. Default is False.
        target_dir: (optional) str, parameter specifying directory to download assets. Default is None.
        file_size: (optional) int, parameter limiting the size of assets to download, in megabytes. Default is None.
        asset_list: (optional) list of str, parameter limiting the types of assets (e.g., agenda, audio, etc.)
                        to be scraped. Default is None.
        csv_export: (optional) str, parameter specifying path to download csv of scraped metadata.
                        Default behavior is not to download a csv unless path is specified.
        append: (optional) bool, True to append metadata to an existing csv, False to overwrite if csv already exists.
                    Default is False.

Returns of scrape(): AssetCollection object.

"""
# Libraries

import re
import datetime
import bs4
import requests

from civic_scraper.scrapers.site import Site
from civic_scraper.asset import Asset, AssetCollection

# Parameters
SUPPORTED_ASSET_TYPES = [
    'agenda',
    'minutes',
    'audio',
    'video',
    'agenda_packet',
    'captions'
]


class CivicPlusSite(Site):
    """
    The CivicPlusSite object returns an AssetCollection object.
    """

    def __init__(self, base_url):
        """
        Creates a CivicPlusSite object

        Input: URL of the form 'https://*.civicplus.com/AgendaCenter', where * is a string specific to the website.
        """
        self.url = base_url
        self.runtime = datetime.datetime.utcnow().date()

    # Public interface (used by calling code)
    def scrape(
            self,
            start_date=None,
            end_date=None,
            download=False,
            target_dir=None,
            file_size=None,
            asset_list=SUPPORTED_ASSET_TYPES,
            csv_export=None,
            append=False,
    ):
        """
        Input:
            start_date: str entered in the form YYYY-MM-DD
            end_date: str entered in the form YYYY-MM-DD
            download: bool, True to download assets identified by scraper. Default is False.
            target_dir: str, optional parameter specifying directory to download assets. Default is None.
            file_size: int, optional parameter limiting the size of assets to download, in megabytes. Default is None.
            asset_list: list of str, optional parameter limiting the types of assets (e.g., agenda, audio, etc.)
                        to be scraped. Default is None.
            csv_export: str, optional parameter specifying path to download csv of scraped metadata.
                        Default behavior is not to download a csv unless path is specified.
            append: bool, True to append metadata to an existing csv, False to overwrite if csv already exists.
                    Default is False.

        Returns:
            AssetCollection object
        """

        html = self._get_html()
        soup = self._make_soup(html)
        post_params = self._get_post_params(soup, start_date, end_date)
        asset_stubs = self._get_all_assets(post_params)
        filtered_stubs = self._filter_assets(asset_stubs, start_date, end_date)
        links = self._make_asset_links(filtered_stubs)
        metadata = self._get_metadata(links)

        if download and csv_export is not None and target_dir is None:
            metadata.download()
            metadata.to_csv(target_path=csv_export, appending=append)
            return metadata
        elif download and csv_export is None and target_dir is None:
            metadata.download()
            return metadata
        elif not download and csv_export is not None:
            metadata.to_csv(target_path=csv_export, appending=append)
            return metadata
        elif target_dir is not None and csv_export is not None:
            metadata.download(target_dir=target_dir, file_size=file_size, asset_list=asset_list)
            metadata.to_csv(target_path=csv_export, appending=append)
            return metadata
        elif target_dir is not None and csv_export is None:
            metadata.download(target_dir=target_dir, file_size=file_size, asset_list=asset_list)
            return metadata
        else:
            return metadata

    # Private methods

    def _get_metadata(self, metadata_dict):
        """
        Returns an AssetCollection object.

        Input: A dictionary of asset URLs, asset titles, meeting ids and meeting names
                (committee_name in the parlance below)
        Output: An AssetCollection object
        """
        assets = []

        for committee in metadata_dict:

            for link in metadata_dict[committee]:

                asset_args = {}
                place = self._get_asset_metadata(r"(?<=-)\w+(?=\.)", self.url)
                asset_args['place'] = place
                state_or_province = self._get_asset_metadata(r"(?<=//)\w{2}(?=-)", self.url)
                asset_args['state_or_province'] = state_or_province
                asset_args['meeting_date'] = datetime.date(int(link[2][5:9]), int(link[2][1:3]), int(link[2][3:5]))
                asset_args['meeting_time'] = None
                asset_args['asset_name'] = link[0]
                asset_args['committee_name'] = committee.strip("►")
                asset_args['meeting_id'] = "civicplus_{}_{}{}".format(state_or_province, place, link[2])
                asset_type = self._get_asset_metadata(r"(?<=e/)\w+(?=/_)", link[1])
                asset_args['asset_type'] = asset_type.lower()
                asset_args['url'] = link[1]
                asset_args['scraped_by'] = 'civicplus.py_1.0.0'
                headers = requests.head(link[1]).headers
                asset_args['content_type'] = headers['content-type']
                asset_args['content_length'] = headers['content-length']
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

    def _get_post_params(self, soup, start_date, end_date):
        """
        Given parsed html text, grabs the bits of html -- a year and a cat_id -- needed
        for the POST request. Filters the list by the years in start_date and end_date.

        Input: Parsed text, start date (YYYY-MM-DD) and end date (YYYY-MM-DD)
        Returns: A dictionary of years, cat_ids and committee names

        The dictionary should fit this format:
        {
            '2015': [(2, "Town Council), (7, "Finance Committee)],
            '2016': [(2, "Town Council)],
        }

        Or more generally: {year: [(cat_id, meeting_name) ... ]}
        """
        year_elements = soup.find_all(class_="listing listingCollapse noHeader")
        years_cat_id = {}
        cat_ids = []

        for element in year_elements:
            meeting_name = element.h2.text.strip("▼")
            a_tags = element.find_all("a")
            for tag in a_tags:
                link = str(tag)
                if link.find("changeYear") != -1:
                    year = re.search(r"(?<=\()\d{4}(?=,)", link).group(0)
        
                    if start_date is not None and end_date is not None:
                        start_year = re.search(r"^\d{4}", start_date).group(0)
                        end_year = re.search(r"^\d{4}", end_date).group(0)
                        if start_year <= year <= end_year:
                            cat_id = re.findall(r"\d+(?=,.*')", link)[1]
                            cat_id_text = (cat_id, meeting_name)
                            cat_ids.append(cat_id_text)
                            years_cat_id[year] = cat_ids
                            
                    elif start_date is not None and end_date is None:
                        start_year = re.search(r"^\d{4}", start_date).group(0)
                        if start_year <= year:
                            cat_id = re.findall(r"\d+(?=,.*')", link)[1]
                            cat_id_text = (cat_id, meeting_name)
                            cat_ids.append(cat_id_text)
                            years_cat_id[year] = cat_ids
                    elif start_date is None and end_date is not None:
                        end_year = re.search(r"^\d{4}", end_date).group(0)
                        if end_year >= year:
                            cat_id = re.findall(r"\d+(?=,.*')", link)[1]
                            cat_id_text = (cat_id, meeting_name)
                            cat_ids.append(cat_id_text)
                            years_cat_id[year] = cat_ids
                    # Case if start_date and end_date are both None
                    else:
                        cat_id = re.findall(r"\d+(?=,.*')", link)[1]
                        cat_id_text = (cat_id, meeting_name)
                        cat_ids.append(cat_id_text)
                        years_cat_id[year] = cat_ids

        return years_cat_id

    def _get_all_assets(self, post_params):
        """
        Given a dictionary of post_params, makes a post request and harvests all of the links from
        the response to that request.

        Input: Dictionary of years, cat_ids and meeting_names
        Returns: Dictionary of asset URLs and URL stubs, meeting_names and asset_names

        The dictionary returned by this function should take the following general structure:

        {
            'meeting_name1':
                [(asset_name, url stub), (asset_name, url stub), ...],
            'meeting_name2':
                [(asset_name, url stub), (asset_name, url stub), ...]
            ...
        }
        """

        page = "{}/UpdateCategoryList".format(self.url)
        # Get links
        links_dict = {}
        for year, committees in post_params.items():
            for committee in committees:
                all_links = [] # Use this to build a list of metadata to populate links_dict
                just_links = [] # Use this to make sure there are no duplicates
                cat_id = committee[0]
                meeting_name = committee[1]
                payload = {'year': year, 'catID': cat_id, 'term': '', 'prevVersionScreen': 'false'}
                response = requests.post(page, params=payload)
                
                # TODO: Remove this if statement?
                if response.status_code == 200:
                    soup = self._make_soup(response.text)
                    end_links = self._get_links(soup)
                    for end_link in end_links:
                        if end_link[1] not in just_links:
                            just_links.append(end_link[1])
                            all_links.append(end_link)
                    links_dict[meeting_name] = all_links

        return links_dict

    def _get_links(self, soup):
        """
        Make a list of links to assets we want to download
        Input: Parsed text of website
        Returns: A list of tuples in which the first item in each tuple is the title of an
                an asset and the second item of the tuple is a link, or partial link, to
                the asset.
        """
        
        rows = soup.find_all(class_='catAgendaRow')
        end_links = []
        for row in rows:
            # Get meeting_id
            meeting_id = row.a['name']
            # Add the first set of links
            asset_list = row.find_all('li')
            asset_title = row.p.text.strip()
            for asset in asset_list:
                end_link = asset.a['href'].strip()
                link_tuple = (asset_title, end_link, meeting_id)
                end_links.append(link_tuple)

            # Add the rest of the links
            tds = row.find_all("td")
            for td in tds[1:-1]:
                
                try:
                    asset_title = td.a['aria-label'].strip()
                except (KeyError, TypeError):
                    asset_title = None
                try:
                    end_link = td.a['href'].strip()
                except (KeyError, TypeError):
                    end_link = None

                if end_link is not None:
                    link_tuple = (asset_title, end_link, meeting_id)
                    end_links.append(link_tuple)

        # Filter out any links that are blank, previous versions of agendas and duplicates
        old_links = []
        for end_link in end_links:
            if (end_link[1] == None) or ('Previous' in end_link[1]):
                end_links.remove(end_link)
            elif end_link[1] in old_links:
                end_links.remove(end_link)
            old_links.append(end_link[1])

        return end_links

    def _filter_assets(self, asset_stubs, start_date, end_date):
        """
        Filters assets to the provided date range.

        Inputs:
            asset_stubs: A dictionary of asset stubs, meeting names, meeting id, and asset titles
            start_date: The earliest date of assets to return
            end_date: The latest date of assets to return

        Returns: A dictionary of asset stubs, asset titles, meeting id and meeting names filtered by date range
        """

        if start_date is not None and end_date is not None:
            start = datetime.date(int(start_date[0:4]), int(start_date[5:7]), int(start_date[-2:]))
            end = datetime.date(int(end_date[0:4]), int(end_date[5:7]), int(end_date[-2:]))
        elif start_date is not None and end_date is None:
            start = datetime.date(int(start_date[0:4]), int(start_date[5:7]), int(start_date[-2:]))
            end = self.runtime + datetime.timedelta(days=14)
        elif start_date is None and end_date is not None:
            start = datetime.date(1900, 1, 1)
            end = datetime.date(int(end_date[0:4]), int(end_date[5:7]), int(end_date[-2:]))
        else:
            start = datetime.date(1900, 1, 1)
            end = self.runtime + datetime.timedelta(days=14)

        filtered_dict = {}
        for committee, stubs in asset_stubs.items():
            filtered_stubs = []
            for stub in stubs:
                year = stub[2][5:9]
                month = stub[2][1:3]
                day = stub[2][3:5]
                date = datetime.date(int(year), int(month), int(day))
                if start <= date <= end:
                    filtered_stubs.append(stub)
            filtered_dict[committee] = filtered_stubs

        # Remove duplicates
        filtered_dict_deduped = {}
        for committee, stubs in filtered_dict.items():
            filtered_stubs_deduped = []
            for stub in stubs:
                if stub not in filtered_stubs_deduped:
                    filtered_stubs_deduped.append(stub)
            filtered_dict_deduped[committee] = filtered_stubs_deduped
        return filtered_dict_deduped

    def _make_asset_links(self, asset_stubs):
        """
        Combines a base URL and a list of partial asset links (asset_stubs)
        to make full urls.

        Input: A dictionary of asset stubs, asset titles, meeting ids and meeting names
        Returns: A dictionary of full URLs, meeting names, meeting ids and asset titles
        """
        url_dict = {}

        for committee in asset_stubs:
            url_list = []
            for stub in asset_stubs[committee]:
                if "/AgendaCenter" in stub[1]:
                    new_stub = stub[1].replace("/AgendaCenter", "")
                    text = "{}{}".format(self.url, new_stub)
                    new_tuple = (stub[0], text, stub[2])
                    url_list.append(new_tuple)
                    url_dict[committee] = url_list
                else:
                    url_list.append(stub)
                    url_dict[committee] = url_list

        return url_dict

    def _get_asset_metadata(self, regex, asset_link):
        """
        Extracts metadata from a provided asset URL.
        Input: Regex to extract metadata
        Returns: Extracted metadata as a string or "no_data" if no metadata is extracted
        """
        if re.search(regex, asset_link) is not None:
            return re.search(regex, asset_link).group(0)
        else:
            return "no_data"

if __name__ == '__main__':
    # The following code is for testing purposes only
    base_url = 'http://wi-columbus.civicplus.com/AgendaCenter'
    site = CivicPlusSite(base_url)
    url_dict = site.scrape(start_date='2020-10-01', end_date='2020-10-09')
    for asset in url_dict:
        print("ASSET: ")
        print("----------------------------")
        print(asset)
        print("----------------------------")