"""
TITLE: CivicPlusSite
AUTHOR: Amy DiPierro
VERSION: 2020-08-26

DESCRIPTION: This module scrapes agendas and minutes from CivicPlus Agenda Center websites. It has one public method, scrape(),
which returns an AssetCollection object.

From Python (example):
    base_url = 'http://ab-slavelake.civicplus.com/AgendaCenter'
    site = CivicPlusSite(base_url)
    url_dict = site.scrape(start_date='2020-06-01', target_dir="/Users/amydipierro/GitHub/tmp/", file_size=20, asset_list=['minutes'])

Inputs of scrape():
        url: str of the form 'https://*.civicplus.com/AgendaCenter', where * is a string specific to the website.
        start_date: (optional) str entered in the form YYYY-MM-DD
        end_date: (optional) str entered in the form YYYY-MM-DD
        file_size: (optional) int, upper limit of size of file to be downloaded, in megabytes.
        asset_list: (optional) list of str containing one or more of the following possible asset types:
                    'agenda', 'minutes', 'audio', 'video', 'agenda_packet', 'captions'.

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
SUPPORTED_ASSET_TYPES = ['agenda', 'minutes', 'audio', 'video', 'agenda_packet', 'captions']


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
        self.runtime = str(datetime.datetime.utcnow().date()).replace('-', '')

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
            append=False
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

    def _get_metadata(self, url_list):
        """
        Returns a list of AssetCollection objects.

        Input: A list of URLs
        Output: A AssetCollection object
        """

        assets = []

        for link in url_list:
            asset_args = {}
            place = self._get_asset_metadata(r"(?<=-)\w+(?=\.)", link)
            asset_args['place'] = place
            state_or_province = self._get_asset_metadata(r"(?<=//)\w{2}(?=-)", link)
            asset_args['state_or_province'] = state_or_province
            meeting_date = self._get_asset_metadata(r"(?<=_)\w{8}(?=-)", link)
            asset_args['meeting_date'] = datetime.date(int(meeting_date[4:]), int(meeting_date[:2]), int(meeting_date[2:4]))
            asset_args['meeting_time'] = None
            asset_args['committee_name'] = None
            meeting_number = self._get_asset_metadata(r"(?<=_)\d{8}-\d{4}", link)
            asset_args['meeting_id'] = "civicplus_{}_{}_{}".format(state_or_province, place, meeting_number)
            asset_type = self._get_asset_metadata(r"(?<=e/)\w+(?=/_)", link)
            asset_args['asset_type'] = asset_type.lower()
            asset_args['url'] = link
            asset_args['scraped_by'] = 'civicplus.py_1.0.0'
            headers = requests.head(link).headers
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
        Returns: A dictionary of years and cat_ids
        """

        # Make the dictionary
        year_elements = soup.find_all(href=re.compile("changeYear"))
        years_cat_id = {}
        cat_ids = []
        for element in year_elements:
            link = element.attrs['href']
            year = re.search(r"(?<=\()\d{4}(?=,)", link).group(0)

            if start_date is not None and end_date is not None:
                start_year = re.search(r"^\d{4}", start_date).group(0)
                end_year = re.search(r"^\d{4}", end_date).group(0)
                if start_year <= year <= end_year:
                    cat_id = re.findall(r"\d+(?=,.*')", link)[1]
                    cat_ids.append(cat_id)
                    years_cat_id[year] = cat_ids
            elif start_date is not None and end_date is None:
                start_year = re.search(r"^\d{4}", start_date).group(0)
                if start_year <= year:
                    cat_id = re.findall(r"\d+(?=,.*')", link)[1]
                    cat_ids.append(cat_id)
                    years_cat_id[year] = cat_ids
            elif start_date is None and end_date is not None:
                end_year = re.search(r"^\d{4}", end_date).group(0)
                if end_year >= year:
                    cat_id = re.findall(r"\d+(?=,.*')", link)[1]
                    cat_ids.append(cat_id)
                    years_cat_id[year] = cat_ids
            # Case if start_date and end_date are both None
            else:
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
        Given a dictionary of post_params, makes a post request and harvests all of the links from
        the response to that request.

        Input: Dictionary of years and catIDs
        Returns: A list of lists of asset URL stubs
        """
        page = "{}/UpdateCategoryList".format(self.url)
        # Get links
        all_links = []
        for year in post_params:
            ids = post_params[year]
            for cat_id in ids:
                payload = {'year': year, 'catID': cat_id, 'term': '', 'prevVersionScreen': 'false'}
                response = requests.post(page, params=payload)
                if response.status_code == 200:
                    soup = self._make_soup(response.text)
                    end_links = self._get_links(soup)
                    all_links.append(end_links)


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

    def _filter_assets(self, asset_stubs, start_date, end_date):
        """
        Filters assets to the provided date range.

        Inputs:
            asset_stubs: A list of asset stubs
            start_date: The earliest date of assets to return
            end_date: The latest date of assets to return
        Returns: A list of asset stubs filtered by date range
        """
        if start_date is not None and end_date is not None:
            start = start_date.replace("-","")
            end = end_date.replace("-", "")
        elif start_date is not None and end_date is None:
            start = start_date.replace("-", "")
            end = self.runtime
        elif start_date is None and end_date is not None:
            start = "19000101"
            end = end_date.replace("-", "")
        else:
            start = "19000101"
            end = self.runtime

        filtered_stubs = []
        for list in asset_stubs:
            for stub in list:
                if re.search(r"(?<=_)\d{2}(?=\d{6}-)", stub) is None:
                    month = ""
                else:
                    month = re.search(r"(?<=_)\d{2}(?=\d{6}-)", stub).group(0)
                if re.search(r"(?<=_\d{2})\d{2}(?=\d{4}-)", stub) is None:
                    day = ""
                else:
                    day = re.search(r"(?<=_\d{2})\d{2}(?=\d{4}-)", stub).group(0)
                if re.search(r"(?<=\d)\d{4}(?=-)", stub) is None:
                    year = ""
                else:
                    year = re.search(r"(?<=\d)\d{4}(?=-)", stub).group(0)
                date = "{}{}{}".format(year, month, day)
                if len(date) == 0:
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
        if re.search(regex, asset_link) is not None:
            return re.search(regex, asset_link).group(0)
        else:
            return "no_data"


if __name__ == '__main__':
    # The following code is for testing purposes only
    base_url = 'http://ab-slavelake.civicplus.com/AgendaCenter'
    site = CivicPlusSite(base_url)
    url_dict = site.scrape(start_date='2020-06-01', target_dir="/Users/amydipierro/GitHub/tmp/", file_size=20, asset_list=['minutes'])


